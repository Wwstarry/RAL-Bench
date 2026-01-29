from __future__ import annotations

import argparse
import cmd
import io
import sys
import traceback
from typing import Any, Optional

from .exceptions import Cmd2ArgparseError
from .parsing import parse_statement


class Cmd2ArgumentParser(argparse.ArgumentParser):
    """ArgumentParser that raises Cmd2ArgparseError instead of exiting."""

    def __init__(self, *args, **kwargs):
        # keep argparse defaults unless overridden
        super().__init__(*args, **kwargs)

    def exit(self, status: int = 0, message: Optional[str] = None):
        usage = ""
        try:
            usage = self.format_usage()
        except Exception:
            usage = ""
        raise Cmd2ArgparseError(message or "", usage=usage, status=status)

    def error(self, message: str):
        usage = ""
        try:
            usage = self.format_usage()
        except Exception:
            usage = ""
        raise Cmd2ArgparseError(message, usage=usage, status=2)


class Cmd2(cmd.Cmd):
    """
    Minimal cmd2-compatible command application.

    - Uses do_<command> dispatch (via cmd.Cmd.onecmd)
    - Adds parsing helpers and poutput/perror convenience methods
    - Disables "repeat last command on empty line" behavior
    """

    prompt = "> "

    def __init__(
        self,
        *,
        stdin=None,
        stdout=None,
        stderr=None,
        completekey: str = "tab",
        use_ipython: bool = False,
        allow_cli_args: bool = True,
        **kwargs: Any,
    ):
        # cmd.Cmd accepts stdin/stdout in Python 3.11+, but for compatibility set manually too.
        super().__init__(completekey=completekey, stdin=stdin, stdout=stdout)
        self.use_ipython = use_ipython
        self.allow_cli_args = allow_cli_args

        self.stdin = stdin if stdin is not None else sys.stdin
        self.stdout = stdout if stdout is not None else sys.stdout
        self.stderr = stderr if stderr is not None else sys.stderr

        # Match cmd2 behavior more closely: do not repeat last command on empty line
        self.lastcmd = ""

    # ---------- output helpers ----------
    def poutput(self, *args, sep: str = " ", end: str = "\n"):
        text = sep.join(str(a) for a in args) + end
        self.stdout.write(text)
        try:
            self.stdout.flush()
        except Exception:
            pass

    def perror(self, *args, sep: str = " ", end: str = "\n"):
        stream = self.stderr if self.stderr is not None else self.stdout
        text = sep.join(str(a) for a in args) + end
        stream.write(text)
        try:
            stream.flush()
        except Exception:
            pass

    def pfeedback(self, *args, sep: str = " ", end: str = "\n"):
        # In cmd2, feedback is typically on stdout.
        self.poutput(*args, sep=sep, end=end)

    # ---------- parsing / dispatch ----------
    def emptyline(self):
        # cmd2: do nothing on empty line
        return False

    def onecmd(self, line: str) -> bool:
        # Keep cmd.Cmd dispatch for compatibility, but pre-parse to support tests and consistent behavior.
        stmt = parse_statement(line)
        if stmt.is_empty:
            return self.emptyline() or False
        # cmd.Cmd.onecmd expects raw line string, not Statement.
        return bool(super().onecmd(stmt.raw))

    def default(self, line: str):
        # cmd.Cmd uses stdout by default; cmd2 generally reports errors.
        self.perror(f"*** Unknown syntax: {line}")

    # ---------- help ----------
    def do_help(self, arg: str):
        # Provide deterministic listing, avoid terminal column formatting.
        arg = (arg or "").strip()
        if not arg:
            names = self.get_names()
            cmds = []
            for name in names:
                if not name.startswith("do_"):
                    continue
                cmdname = name[3:]
                if cmdname.startswith("_"):
                    continue
                if cmdname == "EOF":
                    continue
                cmds.append(cmdname)
            cmds = sorted(set(cmds))
            for c in cmds:
                self.poutput(c)
            return
        # help <command>
        func = getattr(self, "help_" + arg, None)
        if func is not None:
            func()
            return
        do_func = getattr(self, "do_" + arg, None)
        if do_func is None:
            self.perror(f"No help on {arg}")
            return
        doc = do_func.__doc__ or ""
        doc = doc.strip("\n")
        if not doc:
            self.perror(f"No help on {arg}")
            return
        for line in doc.splitlines():
            self.poutput(line.rstrip())

    # ---------- completion ----------
    def completedefault(self, *ignored):
        return []

    def complete_help(self, text, line, begidx, endidx):
        # complete command names for "help <cmd>"
        names = self.get_names()
        cmds = sorted({n[3:] for n in names if n.startswith("do_") and not n[3:].startswith("_")})
        if not text:
            return cmds
        return [c for c in cmds if c.startswith(text)]

    # ---------- argparse integration ----------
    def parse_args(self, parser: argparse.ArgumentParser, args):
        from .parsing import tokenize

        if isinstance(args, str):
            argv = tokenize(args)
        else:
            argv = list(args)
        # Ensure cmd2-like behavior: raise rather than exit if parser is our Cmd2ArgumentParser.
        try:
            return parser.parse_args(argv)
        except SystemExit as e:
            # If a plain argparse parser is used, convert to Cmd2ArgparseError for compatibility.
            usage = ""
            try:
                usage = parser.format_usage()
            except Exception:
                usage = ""
            raise Cmd2ArgparseError("", usage=usage, status=getattr(e, "code", 2))

    # ---------- loop ----------
    def cmdloop(self, intro: Optional[str] = None):
        # Wrap base cmdloop to keep interactive loop alive on exceptions, printing traceback.
        if intro is not None:
            self.intro = intro
        # Implement our own loop for consistent behavior with custom stdin/stdout.
        if self.intro:
            self.poutput(self.intro)
        stop = False
        while not stop:
            try:
                # cmd.Cmd uses self.stdout for prompt output; ensure that is set.
                prompt = self.prompt
                self.stdout.write(prompt)
                try:
                    self.stdout.flush()
                except Exception:
                    pass
                line = self.stdin.readline()
                if line == "":
                    line = "EOF"
                line = line.rstrip("\n")
                try:
                    line = self.precmd(line)
                    stop = self.onecmd(line)
                    stop = self.postcmd(stop, line)
                except Exception:
                    # Print traceback and continue
                    traceback.print_exc(file=self.stderr if self.stderr is not None else self.stdout)
                    stop = False
            except KeyboardInterrupt:
                self.perror("^C")
                stop = False
        return stop