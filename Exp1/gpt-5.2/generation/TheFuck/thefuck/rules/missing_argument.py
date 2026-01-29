from __future__ import annotations

import re
from typing import Iterable, List

from .base import Rule
from ..types import Command


class MissingArgument(Rule):
    name = "missing_argument"
    priority = 80

    def match(self, command: Command) -> bool:
        if command.returncode == 0:
            return False
        out = command.output.lower()
        # Generic patterns for tests: "missing argument", "requires an argument", "expected one argument"
        return any(
            p in out
            for p in (
                "missing argument",
                "requires an argument",
                "expected one argument",
                "too few arguments",
                "the following arguments are required",
            )
        )

    def get_new_command(self, command: Command) -> Iterable[str]:
        # Non-interactive: suggest adding a placeholder "<args>" at end.
        parts = command.script_parts
        if not parts:
            return []
        # If argparse reports required flags or positionals, append "<args>".
        out = command.output
        required: List[str] = []
        m = re.search(r"required:\s*(.+)$", out, flags=re.I | re.M)
        if m:
            required = [x.strip() for x in re.split(r"[,\s]+", m.group(1).strip()) if x.strip()]
        placeholder = " ".join(required) if required else "<args>"
        return [" ".join(parts + [placeholder])]