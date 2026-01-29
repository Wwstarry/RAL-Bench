from __future__ import annotations

from typing import Iterable, List

from .base import Rule
from ..types import Command
from ..utils import closest_commands, parse_unknown_subcommand_from_output, dedupe_preserve_order

# Minimal command -> subcommands map (synthetic/common in tests)
SUBCOMMANDS = {
    "pip": sorted({"install", "uninstall", "list", "show", "freeze", "download", "wheel"}),
    "python": sorted({"-m"}),
    "docker": sorted({"build", "run", "pull", "push", "compose", "images", "ps", "exec"}),
}


def _match(command: Command) -> bool:
    if command.returncode == 0 and "No such subcommand" not in command.output and "not a recognized command" not in command.output:
        return False
    parsed = parse_unknown_subcommand_from_output(command.output)
    if not parsed:
        return False
    tool, sub = parsed
    parts = command.script_parts
    # tool may be missing in message, infer from command
    tool = tool or (parts[0] if parts else "")
    if tool not in SUBCOMMANDS:
        return False
    return sub and sub not in SUBCOMMANDS[tool]


def _get_new_command(command: Command) -> Iterable[str]:
    parsed = parse_unknown_subcommand_from_output(command.output)
    if not parsed:
        return []
    tool, sub = parsed
    parts = command.script_parts
    tool = tool or (parts[0] if parts else "")
    if tool not in SUBCOMMANDS or not parts:
        return []
    # subcommand token usually parts[1]
    if len(parts) < 2:
        return []
    choices = SUBCOMMANDS[tool]
    matches = closest_commands(sub, choices, n=5)
    rest = parts[2:]
    out: List[str] = []
    for m in matches:
        out.append(" ".join([tool, m] + rest))
    return dedupe_preserve_order(out)


RULE = Rule(
    name="misspelled_subcommand",
    match=_match,
    get_new_command=_get_new_command,
    priority=1000,
)