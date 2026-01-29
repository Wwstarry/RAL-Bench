from __future__ import annotations

from typing import Iterable, List, Tuple, Optional
import importlib

# Register built-in rules here in deterministic order
_BUILTIN_RULE_MODULES = [
    "thefuck.rules.sudo",
    "thefuck.rules.unknown_command",
    "thefuck.rules.wrong_subcommand",
    "thefuck.rules.cd",
    "thefuck.rules.missing_hyphen",
    "thefuck.rules.grep_order",
    "thefuck.rules.no_such_file",
]


class Rule:
    """
    Adapter for a rule module.
    Rule module contract:
      - name: str
      - match(command) -> bool
      - suggest(command) -> Iterable[str] or Iterable[(str, int)]
      - optional: priority: int (default 0)
    """
    def __init__(self, module):
        self.module = module
        self.name = getattr(module, "name", module.__name__.split(".")[-1])
        self.default_priority = int(getattr(module, "priority", 0))

    def match(self, command) -> bool:
        return bool(self.module.match(command))

    def suggest(self, command) -> List[Tuple[str, int]]:
        suggestions = self.module.suggest(command)
        result: List[Tuple[str, int]] = []
        if suggestions is None:
            return result
        for s in suggestions:
            if isinstance(s, tuple) and len(s) == 2:
                script, prio = s
            else:
                script, prio = str(s), self.default_priority
            result.append((script, int(prio)))
        return result


def get_rules() -> List[Rule]:
    rules: List[Rule] = []
    for modname in _BUILTIN_RULE_MODULES:
        module = importlib.import_module(modname)
        rules.append(Rule(module))
    return rules