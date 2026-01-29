import os
import importlib


def get_rules():
    """Dynamically load all rules from the rules directory."""
    rules_dir = os.path.join(os.path.dirname(__file__), "rules")
    rule_files = [f for f in os.listdir(rules_dir) if f.endswith(".py") and f != "__init__.py"]

    rules = []
    for rule_file in rule_files:
        module_name = f"thefuck.rules.{rule_file[:-3]}"
        module = importlib.import_module(module_name)
        if hasattr(module, "match") and hasattr(module, "get_new_command"):
            rules.append(module)
    return rules


def match_rule(rule, command):
    """Check if a rule matches the given command."""
    return rule.match(command)


def apply_rule(rule, command):
    """Apply a rule to the given command and return the new command."""
    return rule.get_new_command(command)