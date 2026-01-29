from __future__ import annotations

import re

from ..types import Command
from ..utils import shell_join

priority = 300

_PATTERNS = [
    re.compile(r"missing argument", re.IGNORECASE),
    re.compile(r"requires an argument", re.IGNORECASE),
    re.compile(r"expected (one )?argument", re.IGNORECASE),
    re.compile(r"the following arguments are required", re.IGNORECASE),
    re.compile(r"missing operand", re.IGNORECASE),
]


def match(command: Command) -> bool:
    if command.returncode == 0:
        return False
    text = (command.stderr or "") + "\n" + (command.stdout or "")
    return any(p.search(text) for p in _PATTERNS)


def _fix_cd(command: Command) -> str | None:
    if not command.args:
        return None
    if command.args[0] != "cd":
        return None
    if len(command.args) >= 2:
        return None
    # Deterministic default.
    return shell_join(["cd", ".."])


def _fix_git_commit_m(command: Command) -> str | None:
    # Detect "git commit -m" missing its value.
    if len(command.args) < 3:
        return None
    if command.args[0] != "git" or command.args[1] != "commit":
        return None
    if command.args[-1] == "-m":
        new_args = command.args[:-1] + ["-m", ""]
        return shell_join(new_args)
    # Also handle "... -m" anywhere at end of list with no value
    for i, tok in enumerate(command.args):
        if tok == "-m" and i == len(command.args) - 1:
            new_args = command.args[:i] + ["-m", ""]
            return shell_join(new_args)
    return None


def _fix_trailing_option(command: Command) -> str | None:
    # Generic: if last token looks like an option expecting a value, add "".
    if not command.args:
        return None
    last = command.args[-1]
    if last in {"-m", "-o", "-O", "-u", "-p", "-P", "-c", "-C", "-f", "-F", "--message"}:
        return shell_join(command.args + [""])
    return None


def get_new_command(command: Command) -> str | list[str]:
    for fixer in (_fix_cd, _fix_git_commit_m, _fix_trailing_option):
        out = fixer(command)
        if out:
            return out
    return []