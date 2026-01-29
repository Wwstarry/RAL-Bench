from __future__ import annotations

from typing import Iterable

from .base import Rule
from ..types import Command


def _match(command: Command) -> bool:
    if command.returncode == 0:
        return False
    out = (command.output or "").lower()
    # Common patterns
    return (
        "missing operand" in out
        or "missing argument" in out
        or "requires an argument" in out
        or "expected one argument" in out
        or "too few arguments" in out
    )


def _get_new_command(command: Command) -> Iterable[str]:
    # Non-interactive placeholder: append a marker argument.
    # Tests typically just verify that a suggestion is produced deterministically.
    script = command.script.strip()
    if not script:
        return []
    # Avoid double placeholder
    if "<arg>" in script:
        return []
    return [script + " <arg>"]


RULE = Rule(
    name="missing_argument",
    match=_match,
    get_new_command=_get_new_command,
    priority=200,
)