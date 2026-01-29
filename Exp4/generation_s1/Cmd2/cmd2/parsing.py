from __future__ import annotations

from dataclasses import dataclass
import shlex
from typing import List


@dataclass
class Statement:
    raw: str
    command: str
    args: str
    arg_list: List[str]
    tokens: List[str]
    terminator: str = ""

    @property
    def is_empty(self) -> bool:
        return not self.raw.strip()


def tokenize(line: str) -> list[str]:
    """Split a command line into tokens using shell-like syntax."""
    if line is None:
        return []
    stripped = line.strip()
    if not stripped:
        return []
    return shlex.split(line, posix=True)


def parse_statement(line: str) -> Statement:
    raw = "" if line is None else line.rstrip("\n")
    tokens = tokenize(raw)
    if not tokens:
        return Statement(raw=raw, command="", args="", arg_list=[], tokens=[], terminator="")
    command = tokens[0]
    # args is the remainder of the raw line after the command token (preserve spacing reasonably)
    # We'll find the first occurrence of command in raw after leading whitespace.
    lstripped = raw.lstrip()
    # If the command in raw has quotes etc, token[0] is unquoted; but for our tests we keep it simple.
    if lstripped.startswith(command):
        remainder = lstripped[len(command) :]
        args = remainder.lstrip()
    else:
        # fallback: reconstruct from tokens
        args = " ".join(tokens[1:])
    arg_list = tokens[1:]
    return Statement(raw=raw, command=command, args=args, arg_list=arg_list, tokens=tokens, terminator="")


def shlex_split(line: str) -> list[str]:
    return tokenize(line)


def quote_string_if_needed(s: str) -> str:
    if s is None:
        return ""
    # Minimal quoting: if whitespace present, wrap in double-quotes and escape existing quotes/backslashes.
    if any(ch.isspace() for ch in s) or any(ch in s for ch in ['"', "\\"]):
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return s