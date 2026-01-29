from . import rules
from .models import CorrectedCommand

def get_corrected_commands(command):
    """Get corrected commands for the given failed command."""
    corrections = []
    
    for rule in rules.get_rules():
        if rule.is_match(command):
            corrected = rule.get_new_command(command)
            if isinstance(corrected, str):
                corrected = [corrected]
            
            for cmd in corrected:
                priority = getattr(rule, 'priority', 100)
                corrections.append(CorrectedCommand(cmd, priority=priority))
    
    # Sort by priority (lower = better)
    corrections.sort(key=lambda x: x.priority)
    return corrections