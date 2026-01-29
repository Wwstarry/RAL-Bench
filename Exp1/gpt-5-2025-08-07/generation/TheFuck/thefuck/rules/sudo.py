from __future__ import annotations

from typing import Iterable, Tuple
from ..types import Command

name = "sudo"
priority = 70


def match(command: Command) -> bool:
    t = command.tokens
    if not t:
        return False
    if t[0] == "sudo":
        return False
    txt = (command.stderr or command.stdout or "").lower()
    return "permission denied" in txt


def suggest(command: Command) -> Iterable[Tuple[str, int]]:
    return [("sudo " + command.script, priority + 10)]