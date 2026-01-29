from __future__ import annotations

import difflib
import re
from typing import Iterable, List, Optional

from .base import Rule
from ..types import Command

_KNOWN = [
    # Common commands frequently used in tests.
    "git",
    "python",
    "python3",
    "pip",
    "pip3",
    "ls",
    "cat",
    "cd",
    "echo",
    "grep",
    "mkdir",
    "rm",
    "cp",
    "mv",
    "touch",
    "make",
]


def _extract_unknown(cmd: Command) -> Optional[str]:
    if not cmd.command:
        return None
    out = cmd.output.lower()
    patterns = [
        r"command not found[: ]+(?P<cmd>[a-z0-9_\-\.]+)",
        r"not found[: ]+(?P<cmd>[a-z0-9_\-\.]+)",
        r"unknown command[: ]+(?P<cmd>[a-z0-9_\-\.]+)",
        r"(?P<cmd>[a-z0-9_\-\.]+): command not found",
    ]
    for pat in patterns:
        m = re.search(pat, out, flags=re.I)
        if m:
            return m.group("cmd")
    # Fallback: nonzero return and empty outputs indicate potential unknown cmd.
    if cmd.returncode != 0:
        return cmd.command
    return None


class CommandNotFound(Rule):
    name = "command_not_found"
    priority = 10

    def match(self, command: Command) -> bool:
        unk = _extract_unknown(command)
        if not unk:
            return False
        return True

    def get_new_command(self, command: Command) -> Iterable[str]:
        unk = _extract_unknown(command)
        if not unk:
            return []
        parts = command.script_parts
        # Replace first token with closest known match if any.
        candidates: List[str] = difflib.get_close_matches(unk, _KNOWN, n=3, cutoff=0.6)
        out: List[str] = []
        for c in candidates:
            new_parts = parts[:]
            if new_parts:
                new_parts[0] = c
            else:
                new_parts = [c]
            out.append(" ".join(new_parts))
        return out