from __future__ import annotations

from ..types import Command, Rule
from ..utils import best_by_distance, default_known_commands, looks_like_command_not_found, join_command


def _match(command: Command) -> bool:
    if command.return_code == 0:
        return False
    if not command.name:
        return False
    return looks_like_command_not_found(command.stderr)


def _get_new_command(command: Command) -> list[str]:
    parts = command.parts
    if not parts:
        return []
    name = parts[0]

    # Prefer strict distance for short names, a bit looser for longer.
    max_dist = 2 if len(name) <= 6 else 3
    best = best_by_distance(name, default_known_commands(), max_dist=max_dist)
    if not best or best == name:
        return []
    parts2 = [best] + parts[1:]
    return [join_command(parts2)]


rule = Rule(
    name="command_not_found",
    match=_match,
    get_new_command=_get_new_command,
    priority=500,
)