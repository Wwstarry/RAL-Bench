import re
from difflib import get_close_matches

GIT_COMMANDS = ['add', 'bisect', 'branch', 'checkout', 'clone', 'commit', 'diff',
                'fetch', 'grep', 'init', 'log', 'merge', 'mv', 'pull', 'push',
                'rebase', 'reset', 'rm', 'show', 'status', 'tag']

enabled_by_default = True

def match(command):
    return ('git' in command.script and
            'is not a git command' in command.stderr)

def get_new_command(command):
    match = re.search(r"git: '([^']*)' is not a git command", command.stderr)
    if not match:
        return []

    wrong_cmd = match.group(1)
    if wrong_cmd not in command.script_parts:
        return []

    close_matches = get_close_matches(wrong_cmd, GIT_COMMANDS, n=1, cutoff=0.8)
    if close_matches:
        return command.script.replace(wrong_cmd, close_matches[0], 1)

    return []