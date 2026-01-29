from __future__ import annotations

from typing import Iterable, List

from .base import Rule
from ..types import Command
from ..utils import available_commands, closest_commands, parse_unknown_command_from_output, which


def _match(command: Command) -> bool:
    if command.returncode == 0:
        return False
    out = command.output
    if not out:
        return False
    unk = parse_unknown_command_from_output(out)
    if not unk:
        return False
    # If it actually exists, don't suggest
    return which(unk) is None


def _get_new_command(command: Command) -> Iterable[str]:
    unk = parse_unknown_command_from_output(command.output)
    if not unk:
        return []
    choices = available_commands()
    matches = closest_commands(unk, choices, n=5)
    # Replace only first token
    parts = command.script_parts
    if not parts:
        return []
    rest = parts[1:]
    out: List[str] = []
    for m in matches:
        out.append(" ".join([m] + rest))
    return out


RULE = Rule(
    name="command_not_found",
    match=_match,
    get_new_command=_get_new_command,
    priority=900,
)