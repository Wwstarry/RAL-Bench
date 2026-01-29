from __future__ import annotations

import re

from ..types import Command
from ..utils import levenshtein, shell_join

priority = 100

GIT_SUBCOMMANDS = [
    "add",
    "branch",
    "checkout",
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
    "remote",
    "status",
    "tag",
]

_PATTERNS = [
    re.compile(r"is not a git command", re.IGNORECASE),
    re.compile(r"unknown subcommand", re.IGNORECASE),
    re.compile(r"unknown option", re.IGNORECASE),
]


def match(command: Command) -> bool:
    if command.returncode == 0:
        return False
    if len(command.args) < 2:
        return False
    if command.args[0] != "git":
        return False
    err = (command.stderr or "") + "\n" + (command.stdout or "")
    if any(p.search(err) for p in _PATTERNS):
        return True
    # Also match the canonical message: "git: 'x' is not a git command."
    if "not a git command" in err.lower():
        return True
    return False


def _best_subcommand(token: str) -> str | None:
    best: tuple[int, str] | None = None
    for cand in GIT_SUBCOMMANDS:
        d = levenshtein(token, cand)
        if d > max(2, len(cand) // 2):
            continue
        cur = (d, cand)
        if best is None or cur < best:
            best = cur
    return best[1] if best else None


def get_new_command(command: Command) -> str | list[str]:
    if len(command.args) < 2:
        return []
    wrong = command.args[1]
    replacement = _best_subcommand(wrong)
    if not replacement or replacement == wrong:
        return []
    new_args = ["git", replacement] + command.args[2:]
    return shell_join(new_args)