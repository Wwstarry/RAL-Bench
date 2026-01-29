from thefuck.utils import get_close_matches

GIT_SUBCOMMANDS = ['add', 'branch', 'checkout', 'commit', 'diff', 'log', 'push', 'pull', 'rebase', 'reset', 'status', 'tag']

def match(command):
    return (command.script.startswith('git ') and
            'is not a git command' in command.stderr)

def get_new_command(command):
    parts = command.script_parts
    if len(parts) > 1:
        broken_subcommand = parts[1]
        matches = get_close_matches(broken_subcommand, GIT_SUBCOMMANDS)
        if matches:
            return [command.script.replace(broken_subcommand, match, 1) for match in matches]
    return []

# Higher priority than the generic no_command rule.
priority = 900