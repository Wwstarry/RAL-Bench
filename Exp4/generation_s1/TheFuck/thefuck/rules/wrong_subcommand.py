from __future__ import annotations

import re

from ..types import Command, Rule
from ..utils import best_by_distance, join_command, split_command


_GIT_SUBS = (
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
    "reset",
    "restore",
    "show",
    "stash",
    "status",
    "switch",
    "tag",
)

_PIP_SUBS = (
    "install",
    "uninstall",
    "list",
    "show",
    "freeze",
    "download",
    "wheel",
    "check",
)

_RE_GIT_NOT_A_COMMAND = re.compile(r"git:\s*'([^']+)'\s+is not a git command", re.IGNORECASE)
_RE_PIP_NO_SUCH_COMMAND = re.compile(r"no such command ['\"]?([A-Za-z0-9_-]+)['\"]?", re.IGNORECASE)


def _match(command: Command) -> bool:
    if command.return_code == 0:
        return False
    s = command.stderr or ""
    if _RE_GIT_NOT_A_COMMAND.search(s):
        return True
    if _RE_PIP_NO_SUCH_COMMAND.search(s) and "pip" in split_command(command.command):
        return True
    return False


def _fix_git(command: Command) -> list[str]:
    m = _RE_GIT_NOT_A_COMMAND.search(command.stderr or "")
    if not m:
        return []
    bad = m.group(1)
    best = best_by_distance(bad, _GIT_SUBS, max_dist=2)
    if not best or best == bad:
        return []
    parts = command.parts
    if len(parts) >= 2 and parts[0] == "git":
        parts2 = ["git", best] + parts[2:]
        return [join_command(parts2)]
    # fallback: just suggest git <best>
    return [join_command(["git", best])]


def _fix_pip(command: Command) -> list[str]:
    m = _RE_PIP_NO_SUCH_COMMAND.search(command.stderr or "")
    if not m:
        return []
    bad = m.group(1)
    best = best_by_distance(bad, _PIP_SUBS, max_dist=2)
    if not best or best == bad:
        return []
    parts = command.parts

    # Preserve "python -m pip ..." shape if present.
    if len(parts) >= 3 and parts[0] == "python" and parts[1] == "-m" and parts[2] == "pip":
        if len(parts) >= 4:
            parts2 = parts[:3] + [best] + parts[4:]
        else:
            parts2 = parts[:3] + [best]
        return [join_command(parts2)]

    # Plain pip
    if parts and parts[0] == "pip":
        if len(parts) >= 2:
            parts2 = ["pip", best] + parts[2:]
        else:
            parts2 = ["pip", best]
        return [join_command(parts2)]

    return []


def _get_new_command(command: Command) -> list[str]:
    s = command.stderr or ""
    if _RE_GIT_NOT_A_COMMAND.search(s):
        return _fix_git(command)
    if _RE_PIP_NO_SUCH_COMMAND.search(s):
        return _fix_pip(command)
    return []


rule = Rule(
    name="wrong_subcommand",
    match=_match,
    get_new_command=_get_new_command,
    priority=100,
)