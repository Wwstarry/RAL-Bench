import re
from difflib import get_close_matches
from ..utils import get_all_executables

enabled_by_default = True

def match(command):
    return ('command not found' in command.stderr.lower() or
            'is not recognized as an internal or external command' in command.stderr.lower())

def get_new_command(command):
    # Regex for shells like bash/zsh: "zsh: command not found: gerp"
    not_found_re = re.search(r'([^:]+): command not found: (\S+)', command.stderr)
    if not_found_re:
        wrong_cmd = not_found_re.group(2)
    else:
        # Default to the first part of the script
        wrong_cmd = command.script_parts[0]

    close_matches = get_close_matches(wrong_cmd, get_all_executables(), n=1, cutoff=0.8)
    if close_matches:
        return command.script.replace(wrong_cmd, close_matches[0], 1)

    return []