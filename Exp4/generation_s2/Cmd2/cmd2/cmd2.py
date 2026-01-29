import cmd
import inspect
import io
import os
import traceback
from typing import Any, Callable, Dict, List, Optional, Tuple

from .parsing import Cmd2ArgumentParser, Statement, parse_statement
from . import utils


class Cmd2Error(Exception):
    pass


class Cmd2(cmd.Cmd):
    """
    A small, API-compatible subset of the cmd2.Cmd class.

    Core supported behaviors:
    - do_<command> methods, help_<command> methods, complete_<command> methods
    - improved parsing (Statement) and onecmd_plus_hooks
    - output helpers: poutput, perror, ppaged
    - transcript running via utils.run_transcript (external helper)
    """

    prompt = "(Cmd) "
    intro = None
    ruler = "="

    def __init__(
        self,
        *,
        stdin=None,
        stdout=None,
        stderr=None,
        persistent_history_file: Optional[str] = None,
        allow_cli_args: bool = False,
        **kwargs,
    ):
        super().__init__(stdin=stdin, stdout=stdout, **kwargs)
        self.stderr = stderr if stderr is not None else io.StringIO()
        self.persistent_history_file = persistent_history_file
        self.allow_cli_args = allow_cli_args
        self.last_result: Any = None
        self._last_statement: Optional[Statement] = None

    # ---------- Output helpers ----------
    def poutput(self, msg: Any = "", end: str = "\n") -> None:
        if msg is None:
            msg = ""
        self.stdout.write(str(msg) + end)
        try:
            self.stdout.flush()
        except Exception:
            pass

    def perror(self, msg: Any = "", end: str = "\n") -> None:
        if msg is None:
            msg = ""
        # Match common cmd2 behavior: errors go to stderr if present, else stdout
        target = self.stderr if self.stderr is not None else self.stdout
        target.write(str(msg) + end)
        try:
            target.flush()
        except Exception:
            pass

    def ppaged(self, msg: Any, end: str = "\n") -> None:
        # Minimal: no pager, just output.
        self.poutput(msg, end=end)

    # ---------- Parsing ----------
    def parse_statement(self, line: str) -> Statement:
        st = parse_statement(line)
        return st

    def preparse(self, line: str) -> str:
        return line

    def postparse(self, statement: Statement) -> Statement:
        return statement

    # ---------- Command loop integration ----------
    def onecmd_plus_hooks(self, line: str) -> bool:
        """
        cmd2-style entry point: parse into Statement and run pre/post hooks.
        """
        line = "" if line is None else line
        line = self.preparse(line)

        statement = self.parse_statement(line)
        statement = self.postparse(statement)
        self._last_statement = statement

        stop = False
        try:
            stop = self.onecmd(statement.raw)
        except Exception:
            # cmd2 normally reports errors and continues unless configured otherwise.
            self._report_exception()
            stop = False
        return stop

    def onecmd(self, line: str) -> bool:
        # Override to support empty lines and default cmd.Cmd behavior
        if isinstance(line, Statement):
            line = line.raw
        return super().onecmd(line)

    def default(self, line: str) -> None:
        self.perror(f"*** Unknown syntax: {line}")

    def emptyline(self) -> bool:
        # cmd2 defaults to doing nothing on empty line
        return False

    # ---------- Help ----------
    def get_visible_commands(self) -> List[str]:
        names = []
        for name, _ in inspect.getmembers(self, predicate=callable):
            if name.startswith("do_"):
                cmdname = name[3:]
                if cmdname:
                    names.append(cmdname)
        names.sort()
        return names

    def do_help(self, arg: str) -> None:
        arg = (arg or "").strip()
        if not arg:
            cmds = self.get_visible_commands()
            if cmds:
                self.poutput("Commands:")
                for c in cmds:
                    self.poutput(f"  {c}")
            else:
                self.poutput("No commands.")
            self.poutput('Type "help <command>" for detailed help.')
            return

        func = getattr(self, "help_" + arg, None)
        if callable(func):
            func()
            return

        doc = ""
        do_func = getattr(self, "do_" + arg, None)
        if callable(do_func):
            doc = inspect.getdoc(do_func) or ""
        if doc:
            self.poutput(doc)
        else:
            self.perror(f"No help on {arg}")

    # ---------- Completion ----------
    # cmd.Cmd calls complete_<command> if present, otherwise complete().
    # We'll rely on base cmd implementation.

    # ---------- Built-in commands ----------
    def do_quit(self, arg: str) -> bool:
        """Quit the application."""
        return True

    def do_exit(self, arg: str) -> bool:
        """Exit the application."""
        return True

    def do_EOF(self, arg: str) -> bool:
        return True

    # ---------- Transcript support ----------
    def run_transcript(self, transcript_path: str, *, encoding: str = "utf-8", strip_colors: bool = True):
        text = utils._read_text_file(transcript_path, encoding=encoding)
        return utils.run_transcript(self, text, prompt=self.prompt, strip_colors=strip_colors)

    # ---------- Error reporting ----------
    def _report_exception(self) -> None:
        # Print traceback to stderr in a deterministic way
        tb = traceback.format_exc()
        self.perror(tb.rstrip("\n"))

    # ---------- Convenience for tests ----------
    @property
    def last_statement(self) -> Optional[Statement]:
        return self._last_statement


__all__ = [
    "Cmd2",
    "Cmd2ArgumentParser",
    "Statement",
    "Cmd2Error",
]