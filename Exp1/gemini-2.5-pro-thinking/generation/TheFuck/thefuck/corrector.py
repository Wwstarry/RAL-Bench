import os
from importlib import import_module
from . import const, types

def _get_rules_paths():
    """Returns paths to all rule files."""
    rules_dir = os.path.join(os.path.dirname(__file__), 'rules')
    return [os.path.join(rules_dir, rule) for rule in os.listdir(rules_dir)
            if rule.endswith('.py') and not rule.startswith('_')]

def _load_rule(rule_path):
    """Loads a rule module from a given path."""
    rule_name = os.path.splitext(os.path.basename(rule_path))[0]
    try:
        module_name = 'thefuck.rules.{}'.format(rule_name)
        return import_module(module_name)
    except ImportError:
        return None

def _get_loaded_rules():
    """Loads and returns all enabled rules, sorted for determinism."""
    rules_paths = sorted(_get_rules_paths())
    loaded_rules = []
    for path in rules_paths:
        rule = _load_rule(path)
        if rule and hasattr(rule, 'match') and hasattr(rule, 'get_new_command'):
            loaded_rules.append(rule)
    return loaded_rules

_RULES = _get_loaded_rules()

def get_corrected_commands(command):
    """
    Returns a list of corrected commands for a given failed command.
    """
    corrected_commands = []
    for rule in _RULES:
        if rule.match(command):
            new_commands = rule.get_new_command(command)
            
            # Ensure new_commands is a list
            if isinstance(new_commands, str):
                new_commands = [new_commands]
            
            if isinstance(new_commands, list):
                for cmd_script in new_commands:
                    priority = getattr(rule, 'priority', const.DEFAULT_PRIORITY)
                    corrected_commands.append(
                        types.CorrectedCommand(script=cmd_script, priority=priority)
                    )

    # Remove duplicates and sort by priority (lower is better)
    unique_commands = sorted(list(set(corrected_commands)), key=lambda c: c.priority)
    return unique_commands