from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .settings import Settings
from .types import Command, Rule
from .utils import unique_preserve_order


@dataclass(frozen=True)
class _Suggestion:
    rule_priority: int
    rule_name: str
    index: int
    text: str


def get_suggestions(command: Command, rules: list[Rule], settings: Settings | None = None) -> list[str]:
    settings = settings or Settings()
    suggestions: list[_Suggestion] = []

    for rule in rules:
        if not settings.is_rule_enabled(rule.name, rule.enabled_by_default):
            continue
        try:
            if not rule.match(command):
                continue
        except Exception:
            continue

        try:
            proposed = rule.propose(command)
        except Exception:
            continue

        for idx, text in enumerate(proposed):
            text = (text or "").strip()
            if not text:
                continue
            suggestions.append(_Suggestion(rule.priority, rule.name, idx, text))

    # Deterministic ordering:
    # 1) rule priority
    # 2) rule name (tie-break, stable)
    # 3) within-rule proposal order (idx)
    # 4) suggestion text (final tie-break)
    suggestions.sort(key=lambda s: (s.rule_priority, s.rule_name, s.index, s.text))

    texts = unique_preserve_order(s.text for s in suggestions)
    if settings.max_suggestions is not None:
        texts = texts[: int(settings.max_suggestions)]
    return texts


def get_best_suggestion(command: Command, rules: list[Rule], settings: Settings | None = None) -> str | None:
    sugs = get_suggestions(command, rules, settings=settings)
    return sugs[0] if sugs else None


def suggest(command: Command, rules: Iterable[Rule], settings: Settings | None = None) -> list[str]:
    # Compatibility alias.
    return get_suggestions(command, list(rules), settings=settings)