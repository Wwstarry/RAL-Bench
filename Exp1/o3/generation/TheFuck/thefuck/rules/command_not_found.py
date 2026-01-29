"""
Fixes **typos in the command name** (classic "command not found").

Strategy
--------
1. Observe that
       - exit-status == 127   OR
       - *stderr* contains the words "not found"
2. Fuzzy-match the first word in the command line against executables that are
   found on the current ``$PATH``.
"""
from __future__ import annotations

from ..command import Command
from ..utils import closest_command

priority = 100  # rather high priority – most common error


def match(command: Command) -> bool:
    if command.exit_code == 127:
        return True
    stderr = (command.stderr or "").lower()
    return "command not found" in stderr or "not recognized" in stderr


def get_new_command(command: Command):
    wrong = command.parts[0] if command.parts else ""
    suggestions = closest_command(wrong)
    if not suggestions:
        return []
    # Re-build full command line replacing the first token.
    tail = command.parts[1:]
    corrected_lines = [f"{candidate} {' '.join(tail)}".rstrip() for candidate in suggestions]
    return corrected_lines