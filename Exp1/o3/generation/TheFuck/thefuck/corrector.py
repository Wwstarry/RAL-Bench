"""
High-level convenience wrapper around *rules* that does all the work:
step through all rules, collect suggestions, wrap them in *Correction*
objects and finally sort them by priority and suggestion order.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from .command import Command
from .rules import get_rules


@dataclass(slots=True)
class Correction:
    fixed_script: str
    rule_name: str
    priority: int

    def __str__(self):  # pragma: no cover
        return self.fixed_script


def get_corrected_commands(command: Command) -> List[Correction]:
    """
    Evaluate every rule and assemble a (deterministically ordered) list of
    suggestions.

    The returned list is sorted by

        1. rule.priority   (ascending – i.e. 100 before 1000)
        2. given order of the rule's own suggestions
    """
    corrections: list[Correction] = []
    for rule in get_rules():
        if not rule.match(command):
            continue
        new_cmd = rule.get_new_command(command)
        if not new_cmd:
            continue
        if isinstance(new_cmd, str):
            new_cmd = [new_cmd]
        for idx, cmd_str in enumerate(new_cmd):
            corrections.append(
                Correction(
                    fixed_script=cmd_str,
                    rule_name=rule.name,
                    # Add minor offset to preserve the order *within* a rule.
                    priority=rule.priority * 10 + idx,
                )
            )

    # Final, deterministic ordering
    corrections.sort(key=lambda c: (c.priority, c.fixed_script))
    return corrections