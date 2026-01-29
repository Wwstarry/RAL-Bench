"""
Rule system for TheFuck.
"""

import os
import sys
import importlib
import pkgutil
from typing import Dict, List, Callable, Any, Optional

from thefuck.types import Command
from thefuck.conf import settings


# Type for rule functions
RuleFunction = Callable[[Command], List[str]]

# Dictionary to store registered rules
_rules: Dict[str, RuleFunction] = {}


def register(func: RuleFunction) -> RuleFunction:
    """Decorator to register a rule function."""
    _rules[func.__name__] = func
    return func


def get_rules() -> Dict[str, RuleFunction]:
    """Get all registered rules."""
    if not _rules:
        # Only import rules if they haven't been imported yet
        _import_rules()
    
    # Filter rules based on configuration
    included_rules = settings.get('rules', [])
    excluded_rules = settings.get('exclude_rules', [])
    
    filtered_rules = {}
    for name, func in _rules.items():
        if (not included_rules or name in included_rules) and name not in excluded_rules:
            filtered_rules[name] = func
    
    return filtered_rules


def _import_rules() -> None:
    """Import all modules in the rules package to register rules."""
    # Get the directory of the rules package
    package_dir = os.path.dirname(__file__)
    
    # Import all modules in the package
    for _, name, is_pkg in pkgutil.iter_modules([package_dir]):
        if not is_pkg and name != '__init__':
            try:
                importlib.import_module(f'thefuck.rules.{name}')
            except ImportError:
                # Skip rules that can't be imported
                pass