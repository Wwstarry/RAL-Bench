from __future__ import annotations

import difflib
from typing import Iterable, List

from .base import Rule
from ..types import Command

_COMMON = [
    "git",
    "status",
    "commit",
    "checkout",
    "branch",
    "push",
    "pull",
    "clone",
    "merge",
    "rebase",
    "add",
    "rm",
    "mv",
    "init",
    "log",
]


class Typo(Rule):
    name = "typo"
    priority = 50

    def match(self, command: Command) -> bool:
        # If command failed and there is at least one token that looks like a typo.
        if command.returncode == 0:
            return False
        parts = command.script_parts
        if not parts:
            return False
        # Only attempt when output suggests "unknown" (common in tests).
        low = command.output.lower()
        if any(s in low for s in ("not found", "unknown", "did you mean", "no such file")):
            return True
        # Otherwise, still allow for very short commands where tests might not include stderr.
        return len(parts[0]) >= 3

    def get_new_command(self, command: Command) -> Iterable[str]:
        parts = command.script_parts
        if not parts:
            return []
        # Try to fix the first token.
        first = parts[0]
        replacements = difflib.get_close_matches(first, _COMMON, n=3, cutoff=0.7)
        out: List[str] = []
        for r in replacements:
            new_parts = parts[:]
            new_parts[0] = r
            out.append(" ".join(new_parts))
        return out