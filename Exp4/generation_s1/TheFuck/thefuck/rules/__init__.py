from __future__ import annotations

from ..settings import Settings
from ..types import Rule

from .command_not_found import rule as command_not_found
from .missing_argument import rule as missing_argument
from .option_order import rule as option_order
from .typo_in_command import rule as typo_in_command
from .wrong_subcommand import rule as wrong_subcommand

# Deterministic order: specific -> general
_BUILTIN_RULES: list[Rule] = [
    wrong_subcommand,
    option_order,
    missing_argument,
    typo_in_command,
    command_not_found,
]


def load_rules(settings: Settings | None = None) -> list[Rule]:
    # Settings filtering happens in corrector; keep discovery deterministic.
    return list(_BUILTIN_RULES)


def get_rule_names() -> list[str]:
    return [r.name for r in _BUILTIN_RULES]