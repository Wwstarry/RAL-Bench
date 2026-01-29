from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, List

from ..types import Command

# Rule protocol wrapper


@dataclass(frozen=True)
class Rule:
    name: str
    match: Callable[[Command], bool]
    get_new_command: Callable[[Command], str | list[str]]
    priority: int = 1000


def _load_default_rules() -> list[Rule]:
    # Import locally to keep package import side-effects small and deterministic.
    from . import git_wrong_subcommand, missing_argument, option_ordering, typo_command

    # Deterministic ordering: by priority then name.
    rules = [
        Rule(
            name="git_wrong_subcommand",
            match=git_wrong_subcommand.match,
            get_new_command=git_wrong_subcommand.get_new_command,
            priority=getattr(git_wrong_subcommand, "priority", 100),
        ),
        Rule(
            name="typo_command",
            match=typo_command.match,
            get_new_command=typo_command.get_new_command,
            priority=getattr(typo_command, "priority", 200),
        ),
        Rule(
            name="missing_argument",
            match=missing_argument.match,
            get_new_command=missing_argument.get_new_command,
            priority=getattr(missing_argument, "priority", 300),
        ),
        Rule(
            name="option_ordering",
            match=option_ordering.match,
            get_new_command=option_ordering.get_new_command,
            priority=getattr(option_ordering, "priority", 400),
        ),
    ]
    rules.sort(key=lambda r: (r.priority, r.name))
    return rules


_DEFAULT_RULES: list[Rule] | None = None


def get_rules(settings: object | None = None) -> List[Rule]:
    # settings currently unused, but preserved for API compatibility.
    global _DEFAULT_RULES
    if _DEFAULT_RULES is None:
        _DEFAULT_RULES = _load_default_rules()
    return list(_DEFAULT_RULES)


def iter_rules(settings: object | None = None) -> Iterable[Rule]:
    return get_rules(settings)