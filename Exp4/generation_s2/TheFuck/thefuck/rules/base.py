from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List, Optional

from ..types import Command


@dataclass(frozen=True)
class Rule:
    """
    Minimal Rule protocol.

    name: Rule name
    match: Callable[[Command], bool]
    get_new_command: Callable[[Command], Iterable[str]]
    priority: Higher wins when ordering by rule preference; stable within same.
    """

    name: str
    match: Callable[[Command], bool]
    get_new_command: Callable[[Command], Iterable[str]]
    priority: int = 1000

    def is_match(self, command: Command) -> bool:
        try:
            return bool(self.match(command))
        except Exception:
            return False

    def generate(self, command: Command) -> List[str]:
        try:
            res = self.get_new_command(command)
            if res is None:
                return []
            return list(res)
        except Exception:
            return []