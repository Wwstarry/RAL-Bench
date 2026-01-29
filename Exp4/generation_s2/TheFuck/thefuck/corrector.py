from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

from .types import Command
from .utils import dedupe_preserve_order
from .rules.loader import get_rules


@dataclass(frozen=True)
class Suggestion:
    rule: str
    command: str
    priority: int = 0


def get_suggestions(command: Command, rules=None) -> List[str]:
    """
    Given a failed Command, return a deterministic ordered list of corrected commands.
    """
    rules = rules or get_rules()
    suggestions: List[Suggestion] = []
    for rule in rules:
        if rule.is_match(command):
            for new_cmd in rule.generate(command):
                if new_cmd and new_cmd.strip() and new_cmd.strip() != command.script.strip():
                    suggestions.append(Suggestion(rule=rule.name, command=new_cmd.strip(), priority=rule.priority))

    # Deterministic ordering:
    # 1) higher priority
    # 2) rule name
    # 3) command string
    suggestions_sorted = sorted(
        suggestions, key=lambda s: (-int(s.priority), s.rule, s.command)
    )
    cmds = dedupe_preserve_order([s.command for s in suggestions_sorted])
    return cmds


def get_best_suggestion(command: Command, rules=None) -> Optional[str]:
    suggestions = get_suggestions(command, rules=rules)
    return suggestions[0] if suggestions else None


def get_suggestions_with_metadata(command: Command, rules=None) -> List[Tuple[str, str]]:
    """
    Convenience for tests: list of (rule_name, new_command) in deterministic order.
    """
    rules = rules or get_rules()
    items: List[Suggestion] = []
    for rule in rules:
        if rule.is_match(command):
            for new_cmd in rule.generate(command):
                if new_cmd and new_cmd.strip() and new_cmd.strip() != command.script.strip():
                    items.append(Suggestion(rule=rule.name, command=new_cmd.strip(), priority=rule.priority))
    items = sorted(items, key=lambda s: (-int(s.priority), s.rule, s.command))
    out: List[Tuple[str, str]] = []
    seen = set()
    for it in items:
        key = (it.rule, it.command)
        if key not in seen:
            seen.add(key)
            out.append((it.rule, it.command))
    return out