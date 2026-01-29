import re
from thefuck.utils import get_close_matches, get_all_executables

PATTERNS = [
    'command not found',
    'is not recognized as an internal or external command',
    'No such file or directory',
]

def match(command):
    # Avoid matching on commands that are likely file paths
    if '/' in command.script_parts[0] and 'No such file or directory' in command.stderr:
        return False
        
    for pattern in PATTERNS:
        if pattern in command.stderr:
            return True
    return False

def get_new_command(command):
    broken_cmd = command.script_parts[0]
    executables = get_all_executables()
    close_matches = get_close_matches(broken_cmd, executables)
    
    return [' '.join([match] + command.script_parts[1:]) for match in close_matches]