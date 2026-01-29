from __future__ import annotations

from dataclasses import dataclass, field
from typing import AbstractSet


@dataclass
class Settings:
    non_interactive: bool = True
    require_confirmation: bool = False
    max_suggestions: int = 3
    enabled_rules: AbstractSet[str] | None = None
    disabled_rules: AbstractSet[str] | None = field(default_factory=set)

    def is_rule_enabled(self, name: str, enabled_by_default: bool = True) -> bool:
        if self.enabled_rules is not None:
            return name in self.enabled_rules
        if self.disabled_rules and name in self.disabled_rules:
            return False
        return enabled_by_default