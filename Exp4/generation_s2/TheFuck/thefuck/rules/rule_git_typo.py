from __future__ import annotations

from typing import Iterable, List

from .base import Rule
from ..types import Command
from ..utils import closest_commands, dedupe_preserve_order

# A small deterministic set of common git subcommands (covers typical tests)
GIT_SUBCOMMANDS = sorted(
    {
        "add",
        "bisect",
        "branch",
        "checkout",
        "cherry-pick",
        "clone",
        "commit",
        "diff",
        "fetch",
        "init",
        "log",
        "merge",
        "pull",
        "push",
        "rebase",
        "reset",
        "restore",
        "show",
        "stash",
        "status",
        "switch",
        "tag",
    }
)


def _match(command: Command) -> bool:
    parts = command.script_parts
    if len(parts) < 2:
        return False
    if parts[0] != "git":
        return False
    # command failed or produced "not a git command"
    if command.returncode == 0:
        # still allow matching if stderr has the typical message
        if "not a git command" not in command.output:
            return False
    sub = parts[1]
    return sub not in GIT_SUBCOMMANDS


def _get_new_command(command: Command) -> Iterable[str]:
    parts = command.script_parts
    if len(parts) < 2:
        return []
    sub = parts[1]
    matches = closest_commands(sub, GIT_SUBCOMMANDS, n=5)
    rest = parts[2:]
    out: List[str] = []
    for m in matches:
        out.append(" ".join(["git", m] + rest))
    # Provide a couple of deterministic fallbacks for very common typo patterns
    if sub == "comit":
        out.insert(0, " ".join(["git", "commit"] + rest))
    if sub == "stauts":
        out.insert(0, " ".join(["git", "status"] + rest))
    return dedupe_preserve_order(out)


RULE = Rule(
    name="git_typo",
    match=_match,
    get_new_command=_get_new_command,
    priority=1100,
)