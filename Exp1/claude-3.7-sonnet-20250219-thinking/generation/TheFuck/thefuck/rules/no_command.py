"""Rule to suggest corrections for non-existent commands."""

import difflib
from thefuck.rules import register
from thefuck.types import Command, get_all_executables
from typing import List


@register
def no_command(command: Command) -> List[str]:
    """Suggest corrections for commands that don't exist."""
    if command.return_code != 0 and ('command not found' in command.stderr.lower() or
                                    'not found' in command.stderr.lower()):
        cmd_parts = command.script.split()
        if not cmd_parts:
            return []
        
        cmd = cmd_parts[0]
        executables = get_all_executables()
        
        # Find close matches
        matches = difflib.get_close_matches(cmd, executables, n=3, cutoff=0.6)
        
        suggestions = []
        for match in matches:
            corrected = command.script.replace(cmd, match, 1)
            suggestions.append(corrected)
        
        return suggestions
    
    return []