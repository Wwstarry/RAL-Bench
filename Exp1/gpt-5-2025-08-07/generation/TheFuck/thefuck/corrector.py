from __future__ import annotations

from typing import Iterable, List, Set
from .types import Command, Suggestion
from .rules import get_rules


def get_suggestions(command: Command) -> List[Suggestion]:
    """
    Apply rules to produce a list of suggested fixed commands.
    Suggestions are deterministic and ordered by rule order and rule-provided priority.
    """
    suggestions: List[Suggestion] = []
    seen: Set[str] = set()
    for rule in get_rules():
        try:
            if not rule.match(command):
                continue
            for script, prio in rule.suggest(command):
                if not script or script in seen:
                    continue
                suggestions.append(Suggestion(script=script, priority=prio, rule=rule.name))
                seen.add(script)
        except Exception:
            # Rules must be robust: ignore failures and continue
            continue
    # Stable ordering: primarily by priority (desc) then by insertion order
    suggestions.sort()
    return suggestions