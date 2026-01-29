"""Rules package for TheFuck."""

import os
import importlib
import inspect


def get_rules():
    """Load and return all available rules.
    
    Returns:
        List of rule objects
    """
    rules = []
    rules_dir = os.path.dirname(__file__)
    
    # Get all Python files in the rules directory
    for filename in sorted(os.listdir(rules_dir)):
        if filename.startswith('_') or not filename.endswith('.py'):
            continue
        
        module_name = filename[:-3]
        try:
            module = importlib.import_module(f'thefuck.rules.{module_name}')
            
            # Look for a Rule class or functions
            if hasattr(module, 'match') and hasattr(module, 'get_new_command'):
                rules.append(ModuleRule(module))
        except Exception:
            pass
    
    return rules


class ModuleRule:
    """Wrapper for module-based rules."""
    
    def __init__(self, module):
        self.module = module
        self.priority = getattr(module, 'priority', 1000)
    
    def match(self, command):
        """Check if rule matches the command."""
        return self.module.match(command)
    
    def get_new_command(self, command):
        """Get corrected command(s)."""
        return self.module.get_new_command(command)
    
    def __repr__(self):
        return f'<Rule: {self.module.__name__}>'