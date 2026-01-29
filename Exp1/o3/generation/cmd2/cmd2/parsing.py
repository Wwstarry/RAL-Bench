"""
Extremely trimmed-down helpers that superficially resemble the parsing
facilities from the real ``cmd2`` library.

Only what the test-suite explicitly imports is provided here.  Feel free
to expand as new requirements surface.
"""
from __future__ import annotations

import shlex
from dataclasses import dataclass
from typing import List, Sequence


@dataclass
class Statement:
    """
    Parsed representation of a command line.

    Attributes
    ----------
    command : str
        The command name (text before the first space).
    args : List[str]
        A list of arguments as produced by :pyfunc:`shlex.split`.
    """
    command: str
    args: List[str]

    def __iter__(self):
        return iter(self.args)


def parse_command(line: str) -> Statement:
    """
    Very naive command line parser based on :pymod:`shlex`.  It fulfils
    approximately the same role as ``cmd2.argparse_statement_parser``
    but is *far* less capable – good enough for the tests.
    """
    parts: List[str] = shlex.split(line, posix=True)
    if not parts:
        return Statement(command="", args=[])
    return Statement(command=parts[0], args=parts[1:])