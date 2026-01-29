"""Rules for correcting commands."""

import os
import sys
import importlib.util
from pathlib import Path
from typing import List, Callable, Optional
from thefuck.command import Command


class Rule:
    """Base class for correction rules."""
    
    def __init__(self, name: str, match_fn: Callable, get_corrected_fn: Callable):
        """Initialize a Rule.
        
        Args:
            name: Name of the rule
            match_fn: Function that returns True if rule applies
            get_corrected_fn: Function that returns corrected command(s)
        """
        self.name = name
        self.match = match_fn
        self.get_corrected = get_corrected_fn
    
    def __repr__(self):
        return f"Rule({self.name})"


def load_rules() -> List[Rule]:
    """Load all available rules.
    
    Returns:
        List of Rule objects
    """
    rules = []
    rules_dir = Path(__file__).parent
    
    # Load built-in rules
    for rule_file in sorted(rules_dir.glob("*.py")):
        if rule_file.name.startswith("_"):
            continue
        
        module_name = rule_file.stem
        spec = importlib.util.spec_from_file_location(
            f"thefuck.rules.{module_name}",
            rule_file
        )
        
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
            
            # Check if module has match and get_corrected functions
            if hasattr(module, "match") and hasattr(module, "get_corrected"):
                rule = Rule(
                    name=module_name,
                    match_fn=module.match,
                    get_corrected_fn=module.get_corrected
                )
                rules.append(rule)
    
    return rules