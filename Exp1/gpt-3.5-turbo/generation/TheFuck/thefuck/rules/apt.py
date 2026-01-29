import re
from thefuck.command import Command

rules = []


def match_apt_get_update_needed(command: Command):
    # Detect "E: Could not get lock /var/lib/apt/lists/lock"
    text = command.stderr + command.stdout
    if 'could not get lock' in text.lower() or 'unable to lock' in text.lower():
        return True
    return False


def get_new_command_apt_update(command: Command):
    parts = command.script_parts()
    if not parts:
        return []

    # Suggest to run 'sudo apt-get update' before the command
    # If command already starts with sudo, just prepend apt-get update && 
    if parts[0] == 'sudo':
        new_cmd = 'sudo apt-get update && ' + command.script
    else:
        new_cmd = 'sudo apt-get update && sudo ' + command.script
    return [new_cmd]


def match_apt_command_not_found(command: Command):
    # Detect "E: Command 'foopkg' not found"
    text = command.stderr + command.stdout
    if re.search(r"E: Command '.*' not found", text):
        return True
    return False


def get_new_command_apt_fix(command: Command):
    # No good fix, just suggest sudo apt-get update && original command
    return get_new_command_apt_update(command)


rules.append(
    type('RuleAptGetLock', (), {
        'match': match_apt_get_update_needed,
        'get_new_command': get_new_command_apt_update,
        'priority': 80,
        'description': 'Run apt-get update when lock error',
    })()
)

rules.append(
    type('RuleAptCommandNotFound', (), {
        'match': match_apt_command_not_found,
        'get_new_command': get_new_command_apt_fix,
        'priority': 70,
        'description': 'Fix apt command not found errors',
    })()
)