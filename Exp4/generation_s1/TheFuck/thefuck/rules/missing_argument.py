from __future__ import annotations

import re

from ..types import Command, Rule


_PATTERNS = [
    re.compile(r"missing operand", re.IGNORECASE),
    re.compile(r"expected (?:one|an) argument", re.IGNORECASE),
    re.compile(r"requires an argument", re.IGNORECASE),
    re.compile(r"too few arguments", re.IGNORECASE),
    re.compile(r"the following arguments are required", re.IGNORECASE),
]


def _match(command: Command) -> bool:
    if command.return_code == 0:
        return False
    if not command.parts:
        return False
    s = command.stderr or ""
    return any(p.search(s) for p in _PATTERNS) or (command.parts == ["cd"] and command.return_code != 0)


def _get_new_command(command: Command) -> list[str]:
    parts = command.parts
    if parts == ["cd"]:
        return ["cd ~"]
    return []


rule = Rule(
    name="missing_argument",
    match=_match,
    get_new_command=_get_new_command,
    priority=200,
)