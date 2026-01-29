from __future__ import annotations

import re

from ..types import Command, Rule
from ..utils import best_by_distance, default_known_commands, join_command


_TYPO_HINT_PATTERNS = [
    re.compile(r"^([A-Za-z0-9._-]+): command not found", re.IGNORECASE | re.MULTILINE),
    re.compile(r"'([A-Za-z0-9._-]+)' is not recognized", re.IGNORECASE),
]


def _match(command: Command) -> bool:
    if command.return_code == 0:
        return False
    if not command.name:
        return False
    s = command.stderr or ""
    return any(p.search(s) for p in _TYPO_HINT_PATTERNS)


def _get_new_command(command: Command) -> list[str]:
    parts = command.parts
    if not parts:
        return []
    name = parts[0]
    best = best_by_distance(name, default_known_commands(), max_dist=2)
    if not best or best == name:
        return []
    return [join_command([best] + parts[1:])]


rule = Rule(
    name="typo_in_command",
    match=_match,
    get_new_command=_get_new_command,
    priority=400,
)