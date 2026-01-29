import os
import importlib

def get_rules():
    """
    Discover and load all available rules.
    Returns a list of rule objects (each with match/correct methods).
    """
    rules_dir = os.path.dirname(__file__)
    rule_files = [
        f for f in os.listdir(rules_dir)
        if f.endswith('.py') and f != '__init__.py'
    ]
    rules = []
    for filename in sorted(rule_files):
        modulename = f"thefuck.rules.{filename[:-3]}"
        module = importlib.import_module(modulename)
        if hasattr(module, 'Rule'):
            rules.append(module.Rule())
    return rules

def get_corrections(command, rules):
    """
    Given a Command and a list of rules, return a list of suggested corrections.
    Ordered by rule priority and stability.
    """
    suggestions = []
    for rule in rules:
        if rule.match(command):
            corrections = rule.correct(command)
            if corrections:
                # Each correction is a string
                for c in corrections:
                    suggestions.append((rule.priority, rule.name, c))
    # Sort by priority (lower is better), then rule name, then correction string
    suggestions.sort()
    # Return only the correction strings, in order
    return [c for _, _, c in suggestions]