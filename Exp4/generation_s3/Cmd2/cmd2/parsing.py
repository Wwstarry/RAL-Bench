from __future__ import annotations

import argparse
import shlex
from dataclasses import dataclass
from typing import List, Optional


class Cmd2ArgparseError(Exception):
    """Raised when an argparse parser encounters an error (instead of SystemExit)."""


class Cmd2ShlexError(Exception):
    """Raised when shlex parsing fails (e.g., unmatched quotes)."""


def shlex_split(line: str) -> list[str]:
    try:
        return shlex.split(line, posix=True)
    except ValueError as e:
        raise Cmd2ShlexError(str(e)) from e


@dataclass
class Statement:
    raw: str
    command: str = ""
    args: str = ""
    arg_list: List[str] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.arg_list is None:
            self.arg_list = []

    def __str__(self) -> str:
        return self.raw


class StatementParser:
    def __init__(self, *, allow_comments: bool = True) -> None:
        self.allow_comments = allow_comments

    def parse(self, line: str) -> Statement:
        raw = line if line is not None else ""
        stripped = raw.strip()
        if not stripped:
            return Statement(raw=raw, command="", args="", arg_list=[])

        # Do not strip inline comments; only allow whole-line comment semantics if desired.
        if self.allow_comments and stripped.startswith("#"):
            return Statement(raw=raw, command="", args="", arg_list=[])

        tokens = shlex_split(raw)
        if not tokens:
            return Statement(raw=raw, command="", args="", arg_list=[])

        command = tokens[0]
        arg_list = tokens[1:]

        # Preserve the remainder as a string as cmd.Cmd would provide (roughly).
        # This is a best-effort; cmd2 supports much more. For our purposes, join is OK.
        args = ""
        if len(tokens) > 1:
            # Reconstruct args from original line by locating the first token occurrence.
            # Fallback to joining with spaces if we can't reliably slice.
            try:
                idx = raw.find(command)
                after = raw[idx + len(command) :]
                args = after.lstrip()
            except Exception:
                args = " ".join(arg_list)

        return Statement(raw=raw, command=command, args=args, arg_list=arg_list)


class Cmd2ArgumentParser(argparse.ArgumentParser):
    """argparse parser that raises exceptions instead of exiting."""

    def __init__(self, *args, add_help: bool = True, **kwargs) -> None:
        super().__init__(*args, add_help=add_help, **kwargs)

    def error(self, message: str) -> None:
        raise Cmd2ArgparseError(message)

    def parse_args(self, args: Optional[list[str]] = None, namespace=None):
        return super().parse_args(args=args, namespace=namespace)

    def parse_known_args(self, args: Optional[list[str]] = None, namespace=None):
        return super().parse_known_args(args=args, namespace=namespace)