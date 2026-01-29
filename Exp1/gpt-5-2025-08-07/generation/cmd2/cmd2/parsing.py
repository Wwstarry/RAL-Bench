import shlex
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Statement:
    """
    Lightweight command statement parsed from an input line.

    Attributes:
        raw: original input line
        command: first token (command name)
        args: remainder string after command (unparsed)
        arg_list: list of arguments produced by shlex splitting
        tokens: all tokens including command
    """
    raw: str
    command: str
    args: str
    arg_list: List[str]
    tokens: List[str]

    def __bool__(self):
        return bool(self.command)

    def __str__(self):
        return self.raw


def parse_command(line: str) -> Statement:
    """
    Parse an input command line using shlex for shell-like behavior.

    - Respects quotes
    - Does not expand environment variables
    - Does not support semicolon-chained commands (keep minimal)

    Returns a Statement object.
    """
    if line is None:
        line = ""
    raw = line.strip()
    if not raw:
        return Statement(raw=line, command="", args="", arg_list=[], tokens=[])
    lex = shlex.shlex(line, posix=True)
    lex.whitespace_split = True
    lex.commenters = ""  # don't treat '#' as comment; transcript handles comments separately
    tokens = list(lex)
    if not tokens:
        return Statement(raw=line, command="", args="", arg_list=[], tokens=[])
    command = tokens[0]
    arg_list = tokens[1:]
    # Recreate args string with original quoting preserved where possible
    # Since shlex strips quotes, we fallback to raw minus first token span
    # For compatibility keep simple join
    args = " ".join(arg_list)
    return Statement(raw=line, command=command, args=args, arg_list=arg_list, tokens=tokens)


def join_arg_list(arg_list: List[str]) -> str:
    """Join arg list into a single string with spaces."""
    return " ".join(arg_list or [])


def unquote(s: Optional[str]) -> Optional[str]:
    """Remove symmetric quotes from a string; returns None untouched."""
    if s is None:
        return None
    if len(s) >= 2 and ((s[0] == s[-1] == "'") or (s[0] == s[-1] == '"')):
        return s[1:-1]
    return s