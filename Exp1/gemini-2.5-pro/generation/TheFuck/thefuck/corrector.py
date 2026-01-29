import importlib
import sys
from . import const, types
from .settings import settings

def _get_rules():
    """Imports and returns a list of enabled rule modules."""
    rules = []
    for rule_name in settings.rules:
        try:
            rule_module = importlib.import_module(rule_name)
            if getattr(rule_module, 'enabled_by_default', False):
                rules.append(rule_module)
        except ImportError:
            sys.stderr.write("ERROR: Can't import rule: {}\n".format(rule_name))
    return rules

def _sort_rules(rules):
    """Sorts rules by priority."""
    return sorted(rules, key=lambda rule: getattr(rule, 'priority', const.DEFAULT_PRIORITY))

def get_corrected_commands(command):
    """
    Returns a list of corrected commands for a given command.

    :type command: thefuck.types.Command
    :rtype: list[thefuck.types.CorrectedCommand]
    """
    corrected_commands = []
    for rule in _sort_rules(_get_rules()):
        if rule.match(command):
            new_cmds = rule.get_new_command(command)
            if not isinstance(new_cmds, list):
                new_cmds = [new_cmds]

            for new_cmd in new_cmds:
                if new_cmd:
                    priority = getattr(rule, 'priority', const.DEFAULT_PRIORITY)
                    corrected_commands.append(
                        types.CorrectedCommand(script=new_cmd, side_effect=None, priority=priority)
                    )

    # Remove duplicates and sort by priority
    unique_commands = sorted(
        list(set(corrected_commands)),
        key=lambda c: c.priority)

    return unique_commands