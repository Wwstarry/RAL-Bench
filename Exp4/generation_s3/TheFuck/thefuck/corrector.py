from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from .settings import as_settings
from .types import Command
from .utils import unique_stable
from .rules import get_rules, Rule


@dataclass(frozen=True)
class Suggestion:
    command: str
    rule_name: str
    priority: int = 1000
    confidence: float = 0.0


def _ensure_list(x: str | list[str]) -> list[str]:
    if x is None:
        return []
    if isinstance(x, list):
        return [c for c in x if isinstance(c, str) and c.strip()]
    if isinstance(x, str) and x.strip():
        return [x]
    return []


def get_suggestions(command: Command, settings: object | None = None) -> List[Suggestion]:
    st = as_settings(settings)

    # Default behavior: only correct failing commands unless forced.
    if command.returncode == 0:
        return []

    suggestions: list[Suggestion] = []
    for rule in get_rules(st):
        try:
            if not rule.match(command):
                continue
            new_cmds = _ensure_list(rule.get_new_command(command))
            for new_cmd in new_cmds:
                suggestions.append(
                    Suggestion(
                        command=new_cmd,
                        rule_name=rule.name,
                        priority=rule.priority,
                        confidence=0.0,
                    )
                )
        except Exception:
            # Deterministic, quiet failure: skip broken rule.
            continue

    # De-duplicate by command string, first win (stable).
    unique_cmds = unique_stable([s.command for s in suggestions])
    by_cmd: dict[str, Suggestion] = {}
    for s in suggestions:
        if s.command in unique_cmds and s.command not in by_cmd:
            by_cmd[s.command] = s

    uniq_suggestions = [by_cmd[c] for c in unique_cmds if c in by_cmd]

    # Stable ordering: priority asc, confidence desc, command lex.
    uniq_suggestions.sort(key=lambda s: (s.priority, -float(s.confidence), s.command))
    if st.max_suggestions is not None:
        uniq_suggestions = uniq_suggestions[: max(0, int(st.max_suggestions))]
    return uniq_suggestions


def get_corrected_commands(command: Command, settings: object | None = None) -> list[str]:
    return [s.command for s in get_suggestions(command, settings)]