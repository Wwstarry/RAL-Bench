from __future__ import annotations

from typing import Iterable

from .base import Rule
from ..types import Command


class Sudo(Rule):
    name = "sudo"
    priority = 20

    def match(self, command: Command) -> bool:
        if command.returncode == 0:
            return False
        out = command.output.lower()
        # Common permission errors.
        if "permission denied" in out or "operation not permitted" in out:
            # Avoid double sudo.
            return not command.script.strip().startswith("sudo ")
        return False

    def get_new_command(self, command: Command) -> Iterable[str]:
        return [f"sudo {command.script.strip()}"]