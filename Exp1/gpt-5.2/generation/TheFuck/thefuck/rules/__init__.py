from __future__ import annotations

from typing import Dict, Iterable, List, Type

from .base import Rule

# Built-in rules for tests.
from . import command_not_found  # noqa: F401
from . import typo  # noqa: F401
from . import git  # noqa: F401
from . import missing_argument  # noqa: F401
from . import sudo  # noqa: F401


def get_rules() -> List[Rule]:
    """
    Discover rules.

    The real project loads rules from files; here we keep a deterministic set.
    """
    rules: List[Rule] = []
    for cls in Rule.__subclasses__():
        # Only include classes from our package (avoid weird test imports).
        if cls.__module__.startswith("thefuck.rules."):
            rules.append(cls())
    rules.sort(key=lambda r: r.name)
    return rules


def get_rule_names() -> List[str]:
    return [r.name for r in get_rules()]


def get_rules_dict() -> Dict[str, Rule]:
    return {r.name: r for r in get_rules()}


__all__ = ["Rule", "get_rules", "get_rule_names", "get_rules_dict"]