from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

from ..types import Command


@dataclass
class Rule:
    """
    Minimal rule protocol.

    - name: rule identifier
    - priority: lower numbers are preferred (sorted first)
    - match(command): bool
    - get_new_command(command): yields candidate corrected command strings
    """

    name: str = "base"
    priority: int = 1000
    enabled_by_default: bool = True

    def match(self, command: Command) -> bool:
        return False

    def get_new_command(self, command: Command) -> Iterable[str]:
        return []

    def __call__(self, command: Command) -> List[str]:
        if not self.match(command):
            return []
        res = list(self.get_new_command(command))
        # Ensure deterministic and de-duplicated ordering.
        seen = set()
        out: List[str] = []
        for s in res:
            if s and s not in seen:
                seen.add(s)
                out.append(s)
        return out