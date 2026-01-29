import os

def _get_rules_from_paths(paths):
    """Yields rule modules from paths."""
    rules = set()
    for path in paths:
        if not os.path.isdir(path):
            continue
        for file in os.listdir(path):
            if file.endswith('.py') and not file.startswith('_'):
                rule_name = file[:-3]
                rules.add('thefuck.rules.{}'.format(rule_name))
    return sorted(list(rules))

def _get_settings():
    """
    Creates a settings object. In a real app, this would be configurable.
    For this implementation, we use defaults and discover rules.
    """
    settings_obj = type('Settings', (), {})()

    # Non-interactive mode for tests
    settings_obj.require_confirmation = False

    # Rule discovery
    rule_path = os.path.join(os.path.dirname(__file__), 'rules')
    settings_obj.rules = _get_rules_from_paths([rule_path])

    # Rule priorities (can be overridden)
    settings_obj.priority = {}

    return settings_obj

# Global settings object, loaded on import.
settings = _get_settings()