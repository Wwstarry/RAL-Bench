from __future__ import annotations

from ..types import Command
from ..utils import contains_command_not_found, levenshtein, shell_join

priority = 200

# Small built-in dictionary of common commands.
KNOWN_COMMANDS = [
    "git",
    "python",
    "pip",
    "ls",
    "cd",
    "mkdir",
    "rm",
    "mv",
    "cp",
    "cat",
    "echo",
]


def match(command: Command) -> bool:
    if not command.args:
        return False
    if command.returncode == 0:
        return False
    combined = (command.stdout or "") + "\n" + (command.stderr or "")
    if not contains_command_not_found(combined):
        return False
    # Only trigger when command name doesn't look known already.
    return command.args[0] not in KNOWN_COMMANDS


def _best_replacement(token: str) -> str | None:
    token = token or ""
    best: tuple[int, str] | None = None
    for cand in KNOWN_COMMANDS:
        d = levenshtein(token, cand)
        # Only accept reasonably close candidates.
        if d > max(2, len(cand) // 2):
            continue
        cur = (d, cand)
        if best is None or cur < best:
            best = cur
    return best[1] if best else None


def get_new_command(command: Command) -> str | list[str]:
    if not command.args:
        return []
    replacement = _best_replacement(command.args[0])
    if not replacement:
        return []
    new_args = [replacement] + command.args[1:]
    return shell_join(new_args)