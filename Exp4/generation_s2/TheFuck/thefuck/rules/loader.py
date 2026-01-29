from __future__ import annotations

from typing import List

from .base import Rule
from .rule_git_typo import RULE as GIT_TYPO
from .rule_command_not_found import RULE as COMMAND_NOT_FOUND
from .rule_misspelled_subcommand import RULE as MISSPELLED_SUBCOMMAND
from .rule_missing_argument import RULE as MISSING_ARGUMENT
from .rule_option_order import RULE as OPTION_ORDER


def get_rules() -> List[Rule]:
    # Deterministic order: priority then name.
    rules = [
        GIT_TYPO,
        MISSPELLED_SUBCOMMAND,
        COMMAND_NOT_FOUND,
        MISSING_ARGUMENT,
        OPTION_ORDER,
    ]
    return sorted(rules, key=lambda r: (-int(getattr(r, "priority", 0)), r.name))