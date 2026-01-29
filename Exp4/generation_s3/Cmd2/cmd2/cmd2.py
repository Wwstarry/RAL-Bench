from __future__ import annotations

import cmd
import inspect
import io
import os
import sys
import traceback
from contextlib import redirect_stdout
from typing import Optional

from .parsing import StatementParser
from .transcript import run_transcript
from .utils import StdSim, normalize_newlines, strip_ansi


class Cmd2(cmd.Cmd):
    prompt: str = "(cmd) "
    intro: Optional[str] = None

    def __init__(
        self,
        completekey: str = "tab",
        stdin=None,
        stdout=None,
        *,
        allow_cli_args: bool = False,
        **kwargs,
    ) -> None:
        super().__init__(completekey=completekey, stdin=stdin, stdout=stdout, **kwargs)
        self.allow_cli_args = allow_cli_args
        self.debug: bool = False
        self.statement_parser = StatementParser(allow_comments=True)

        if self.stdin is None:
            self.stdin = sys.stdin
        if self.stdout is None:
            self.stdout = sys.stdout

        # cmd.Cmd uses use_rawinput; in non-tty contexts it should be False to avoid hanging.
        try:
            self.use_rawinput = bool(getattr(self.stdin, "isatty", lambda: False)())
        except Exception:
            self.use_rawinput = False

        # place to store diffs when fail_on_diff=False
        self.transcript_diffs: list[tuple[str, str]] = []

    # ---------- output helpers ----------
    def poutput(self, msg: object = "", *, end: str = "\n") -> None:
        s = "" if msg is None else str(msg)
        self.stdout.write(s + end)

    def perror(self, msg: object = "", *, end: str = "\n") -> None:
        # For simplicity and test determinism, route to stdout
        self.poutput(msg, end=end)

    # ---------- command discovery/help ----------
    def get_all_commands(self) -> list[str]:
        cmds = []
        for name in dir(self):
            if name.startswith("do_") and name != "do_help":
                cmds.append(name[3:])
        # include help explicitly
        cmds.append("help")
        # de-dup & sort
        return sorted(set(cmds))

    def get_help(self, command: str) -> str:
        if not command:
            return ""
        meth = getattr(self, f"do_{command}", None)
        if meth is None:
            return f"No help on {command}"
        doc = inspect.getdoc(meth) or ""
        if doc:
            return doc
        return f"No help on {command}"

    def do_help(self, arg: str) -> None:
        arg = (arg or "").strip()
        if not arg:
            for c in self.get_all_commands():
                self.poutput(c)
            return
        self.poutput(self.get_help(arg))

    # ---------- parsing / dispatch ----------
    def parseline(self, line: str):
        # Keep cmd.Cmd compatible behavior but avoid repeating previous command.
        if line is None:
            return None, None, None
        line_stripped = line.strip()
        if not line_stripped:
            return None, None, line

        # Accept standard cmd.Cmd parsing: command is first token separated by whitespace.
        # Also strip leading spaces.
        s = line.lstrip()
        i = 0
        while i < len(s) and not s[i].isspace():
            i += 1
        cmdname = s[:i]
        arg = s[i:].strip() if i < len(s) else ""
        return cmdname, arg, line

    def emptyline(self):
        # Do nothing; do not repeat last command
        return False

    def default(self, line: str) -> None:
        cmdname, _, _ = self.parseline(line)
        if cmdname:
            self.poutput(f"Unknown command: {cmdname}")
        else:
            self.poutput("Unknown command")

    def execute_command(self, line: str):
        return self.onecmd(line)

    def onecmd(self, line: str):
        # Largely mirrors cmd.Cmd.onecmd, but with exception handling and deterministic errors.
        line = "" if line is None else line

        cmdname, arg, _ = self.parseline(line)
        if cmdname is None:
            return self.emptyline()

        # Use cmd.Cmd's built-in precmd/postcmd if present
        try:
            line2 = self.precmd(line)
        except Exception:
            line2 = line
        cmdname, arg, _ = self.parseline(line2)
        if cmdname is None:
            stop = self.emptyline()
            try:
                self.postcmd(stop, line2)
            except Exception:
                pass
            return stop

        func = getattr(self, "do_" + cmdname, None)
        if func is None:
            self.default(line2)
            try:
                return self.postcmd(False, line2)
            except Exception:
                return False

        try:
            stop = func(arg or "")
        except Exception as e:
            if self.debug:
                raise
            self.perror(f"{type(e).__name__}: {e}")
            stop = False

        try:
            stop = self.postcmd(stop, line2)
        except Exception:
            # If postcmd fails, keep loop going unless in debug
            if self.debug:
                raise
            self.perror("Error in postcmd")
            stop = False
        return stop

    # ---------- completion ----------
    def completenames(self, text: str, *ignored):
        cmds = self.get_all_commands()
        return [c for c in cmds if c.startswith(text)]

    def complete(self, text: str, state: int):
        # Use cmd.Cmd.complete, but ensure missing readline doesn't crash
        try:
            return super().complete(text, state)
        except Exception:
            # Fallback: just provide command name completion from completenames
            matches = self.completenames(text)
            try:
                return matches[state]
            except IndexError:
                return None

    # ---------- built-in exit commands ----------
    def do_quit(self, arg: str) -> bool:
        """Quit the application."""
        return True

    def do_exit(self, arg: str) -> bool:
        """Exit the application."""
        return True

    def do_EOF(self, arg: str) -> bool:
        """Exit on EOF (Ctrl-D)."""
        # Many shells print a newline on EOF; keep it optional but harmless.
        self.poutput("")
        return True

    # ---------- scripting / transcripts ----------
    def run_script(self, script: str, *, echo: bool = False, stop_on_error: bool = False) -> str:
        # Capture output produced during script execution, regardless of configured stdout.
        buf = StdSim()
        old_stdout = self.stdout
        self.stdout = buf
        try:
            script = normalize_newlines(script)
            for line in script.split("\n"):
                if line == "":
                    continue
                if echo:
                    self.poutput(self.prompt + line)
                try:
                    stop = self.onecmd(line)
                except Exception:
                    if self.debug:
                        raise
                    traceback.print_exc(file=buf)
                    stop = False
                if stop:
                    break
        finally:
            self.stdout = old_stdout
        return buf.getvalue()

    def run_transcript_tests(
        self,
        transcript_files,
        *,
        fail_on_diff: bool = True,
        encoding: str = "utf-8",
    ) -> int:
        self.transcript_diffs.clear()
        failures = 0
        for path in list(transcript_files):
            passed, diff = run_transcript(self, path, encoding=encoding)
            if not passed:
                failures += 1
                self.transcript_diffs.append((path, diff))
                if fail_on_diff:
                    raise AssertionError(diff)
        return failures

    # ---------- loop ----------
    def cmdloop(self, intro: str | None = None) -> None:
        # Rely on cmd.Cmd.cmdloop; ensure intro printed to our stdout.
        if intro is None:
            intro = self.intro
        if intro:
            self.poutput(intro, end="\n")

        # cmd.Cmd.cmdloop prints prompt and reads; for non-interactive stdin, it will read lines.
        # Ensure it uses our stdout by keeping self.stdout set.
        return super().cmdloop(intro="")  # we've already printed intro