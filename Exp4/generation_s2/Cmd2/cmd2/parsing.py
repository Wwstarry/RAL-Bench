import argparse
import shlex
from dataclasses import dataclass
from typing import Any, List, Optional, Sequence, Tuple


@dataclass
class Statement:
    raw: str
    command: str = ""
    args: str = ""
    arg_list: List[str] = None

    def __post_init__(self):
        if self.arg_list is None:
            self.arg_list = []


class Cmd2ArgumentParser(argparse.ArgumentParser):
    """
    Minimal compatibility wrapper around argparse.ArgumentParser used by cmd2.

    Differences from argparse:
    - Raises ValueError (or Cmd2ArgumentError) instead of exiting on error.
    """

    def __init__(self, *args, **kwargs):
        self._cmd2_silent = kwargs.pop("silent", False)
        super().__init__(*args, **kwargs)

    def error(self, message):
        # argparse normally prints usage and exits; cmd2 typically reports error.
        raise ValueError(message)

    def exit(self, status=0, message=None):
        if message:
            raise ValueError(message)
        raise ValueError(f"Parser exited with status {status}")


def tokenize(line: str) -> List[str]:
    """
    Tokenize an input line similar to cmd2's parsing with shlex.
    """
    if line is None:
        return []
    line = line.strip()
    if line == "":
        return []
    return shlex.split(line, posix=True)


def parse_statement(line: str) -> Statement:
    raw = line if line is not None else ""
    s = Statement(raw=raw)
    toks = tokenize(raw)
    if not toks:
        s.command = ""
        s.args = ""
        s.arg_list = []
        return s
    s.command = toks[0]
    s.arg_list = toks[1:]
    # Reconstruct args string faithfully enough for tests
    s.args = raw[len(raw.split(None, 1)[0]) :].lstrip() if raw.strip() else ""
    return s


def split_command_and_args(line: str) -> Tuple[str, str]:
    st = parse_statement(line)
    return st.command, st.args


def argparse_parse(parser: argparse.ArgumentParser, arg_list: Sequence[str]) -> Any:
    """
    Parse args via argparse without exiting; convert argparse's SystemExit into ValueError.
    """
    try:
        return parser.parse_args(list(arg_list))
    except SystemExit as e:
        raise ValueError(str(e)) from None


__all__ = [
    "Statement",
    "Cmd2ArgumentParser",
    "tokenize",
    "parse_statement",
    "split_command_and_args",
    "argparse_parse",
]