from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Sequence, Tuple

from .types import Command
from .rules import Rule, get_rules


@dataclass(frozen=True)
class Suggestion:
    command: str
    rule: str
    priority: int


def _collect(command: Command, rules: Sequence[Rule]) -> List[Suggestion]:
    suggestions: List[Suggestion] = []
    for rule in rules:
        if not rule.enabled_by_default:
            continue
        for new_cmd in rule(command):
            suggestions.append(Suggestion(command=new_cmd, rule=rule.name, priority=rule.priority))
    # Deterministic sorting: priority, rule name, command string.
    suggestions.sort(key=lambda s: (s.priority, s.rule, s.command))
    # De-duplicate by command while keeping first (best) occurrence.
    seen = set()
    out: List[Suggestion] = []
    for s in suggestions:
        if s.command not in seen:
            seen.add(s.command)
            out.append(s)
    return out


def get_corrected_commands(
    command: Command,
    rules: Optional[Sequence[Rule]] = None,
    limit: Optional[int] = None,
) -> List[str]:
    """
    Return list of suggested corrected command strings ordered by preference.
    """
    rules = list(rules) if rules is not None else get_rules()
    suggestions = _collect(command, rules)
    cmds = [s.command for s in suggestions]
    if limit is not None:
        cmds = cmds[: max(0, int(limit))]
    return cmds


def get_suggestions_with_metadata(
    command: Command,
    rules: Optional[Sequence[Rule]] = None,
    limit: Optional[int] = None,
) -> List[Suggestion]:
    rules = list(rules) if rules is not None else get_rules()
    suggestions = _collect(command, rules)
    if limit is not None:
        suggestions = suggestions[: max(0, int(limit))]
    return suggestions