import re

def match(command):
    return ('git' in command.script and
            'push' in command.script and
            'fatal: The current branch' in command.stderr and
            'has no upstream branch' in command.stderr)

def get_new_command(command):
    match = re.search(r"git push --set-upstream (\w+) (\w+)", command.stderr)
    if match:
        return [match.group(0)]
    return []