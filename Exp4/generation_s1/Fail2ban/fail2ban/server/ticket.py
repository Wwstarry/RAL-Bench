from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class Ticket:
    ip: str
    time: float
    line: str
    pattern: str