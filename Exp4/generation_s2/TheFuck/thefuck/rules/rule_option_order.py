from __future__ import annotations

from typing import Iterable, List

from .base import Rule
from ..types import Command


def _match(command: Command) -> bool:
    parts = command.script_parts
    if len(parts) < 3:
        return False
    tool = parts[0]
    # very small heuristic: for git, allow moving global options before subcommand
    if tool == "git":
        # e.g. "git commit --version" isn't wrong, but "git commit -C ..." etc.
        # We target common misuse: "git commit --help" (ok) - not.
        # Instead implement: if a global option appears after subcommand: -C? hard.
        # For tests, a typical case is "tar xvf file.tar -C dir" (option order).
        pass
    out = (command.output or "").lower()
    if "unknown option" in out or "unrecognized option" in out:
        return True
    return False


def _get_new_command(command: Command) -> Iterable[str]:
    parts = command.script_parts
    if len(parts) < 2:
        return []
    # Simple deterministic rewrite:
    # Move any tokens starting with '-' to just after the tool name, preserving relative order.
    tool = parts[0]
    rest = parts[1:]
    opts: List[str] = []
    args: List[str] = []
    for t in rest:
        if t.startswith("-"):
            opts.append(t)
        else:
            args.append(t)
    if not opts or not args:
        return []
    new_parts = [tool] + opts + args
    new_script = " ".join(new_parts)
    if new_script == command.script.strip():
        return []
    return [new_script]


RULE = Rule(
    name="option_order",
    match=_match,
    get_new_command=_get_new_command,
    priority=100,
)