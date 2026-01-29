import re

def match(command):
    return ('git' in command.script and
            'branch' in command.script and
            "A branch named '" in command.stderr and
            "' already exists" in command.stderr)

def get_new_command(command):
    match = re.search(r"A branch named '([^']*)' already exists", command.stderr)
    if match:
        branch_name = match.group(1)
        return f'git checkout {branch_name}'
    return []