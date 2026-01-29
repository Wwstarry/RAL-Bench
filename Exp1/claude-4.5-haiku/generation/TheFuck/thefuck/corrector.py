"""Core correction logic."""

from typing import List
from thefuck.command import Command
from thefuck.rules import load_rules


def get_corrected_commands(command: Command) -> List[str]:
    """Get corrected command suggestions for a failed command.
    
    Args:
        command: The Command object representing the failed command
        
    Returns:
        List of corrected command strings, ordered by preference
    """
    rules = load_rules()
    corrected = []
    
    for rule in rules:
        try:
            if rule.match(command):
                suggestions = rule.get_corrected(command)
                if suggestions:
                    if isinstance(suggestions, str):
                        corrected.append(suggestions)
                    else:
                        corrected.extend(suggestions)
        except Exception:
            # Silently skip rules that error
            pass
    
    return corrected