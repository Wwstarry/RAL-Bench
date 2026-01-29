"""
Rule discovery mechanism.

A "rule" is simply a python module placed into this ``rules`` package that
provides at least two callables:

    match(command: Command) -> bool
        Return True if the rule is applicable.

    get_new_command(command: Command) -> str | list[str]
        Return the corrected command(s).  Multiple suggestions are allowed –
        they will be turned into individual Correction objects.

A rule *may* also expose a ``priority`` attribute (integer, lower == better).
If missing, default priority ``1000`` is assumed.
"""
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path
from types import ModuleType
from typing import Iterable, List

from ..command import Command

_RULES_PACKAGE = __name__  # i.e. "thefuck.rules"


class Rule:
    """
    Light wrapper around a rule module, making life easier for the rest of the
    code that only needs *behaviour* and does not care about *where* the rule
    lives on disk.
    """

    __slots__ = ("module", "priority", "name")

    def __init__(self, module: ModuleType):
        self.module = module
        self.name = module.__name__.rsplit(".", 1)[-1]
        self.priority = getattr(module, "priority", 1000)

    # --------------------------------------------------------------------- #
    # Passthrough helpers
    # --------------------------------------------------------------------- #
    def match(self, command: Command) -> bool:
        return bool(self.module.match(command))

    def get_new_command(self, command: Command):
        return self.module.get_new_command(command)

    # --------------------------------------------------------------------- #
    # Duck-typing niceties — Convenience
    # --------------------------------------------------------------------- #
    def __repr__(self):  # pragma: no cover
        return f"<Rule {self.name} priority={self.priority}>"


def _discover_rule_module_names() -> Iterable[str]:
    """
    Iterate over dotted-module-names below ``thefuck.rules`` – packages and
    *private* modules (prefixed with an underscore) are ignored.
    """
    pkg_path = Path(__file__).with_suffix("")  # directory of this __init__.py
    for module_info in pkgutil.iter_modules([str(pkg_path.parent)]):
        if module_info.ispkg:
            continue
        name = module_info.name
        if name.startswith("_"):
            continue
        yield f"{_RULES_PACKAGE}.{name}"


def get_rules() -> List[Rule]:
    """
    Import and wrap every rule shipped in ``thefuck.rules``.
    Returned list is **sorted** by the rule's priority (ascending).
    """
    rules: list[Rule] = []
    for dotted_name in _discover_rule_module_names():
        mod = importlib.import_module(dotted_name)
        rules.append(Rule(mod))

    # Stable ordering: first by priority, second by name
    rules.sort(key=lambda r: (r.priority, r.name))
    return rules