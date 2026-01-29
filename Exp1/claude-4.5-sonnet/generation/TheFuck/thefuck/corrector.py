"""Core correction logic for TheFuck."""

from thefuck.types import Command
from thefuck import rules


def get_corrected_commands(command):
    """Get corrected commands for a failed command.
    
    Args:
        command: Command object representing the failed command
        
    Returns:
        List of corrected command strings, ordered by preference
    """
    if not isinstance(command, Command):
        return []
    
    corrections = []
    
    # Load all rules and try to match
    all_rules = rules.get_rules()
    
    for rule in all_rules:
        if rule.match(command):
            new_cmds = rule.get_new_command(command)
            
            # Handle both single string and list returns
            if isinstance(new_cmds, str):
                new_cmds = [new_cmds]
            elif not isinstance(new_cmds, list):
                continue
            
            for cmd in new_cmds:
                if cmd and cmd not in corrections:
                    corrections.append(cmd)
    
    return corrections