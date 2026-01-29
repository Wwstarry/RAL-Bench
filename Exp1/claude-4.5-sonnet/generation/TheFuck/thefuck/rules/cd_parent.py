"""Rule for cd .. typos."""


def match(command):
    """Match cd.. without space."""
    return command.script in ('cd..', 'cd...')


def get_new_command(command):
    """Correct to cd .. or cd ../.."""
    if command.script == 'cd..':
        return 'cd ..'
    elif command.script == 'cd...':
        return 'cd ../..'
    return command.script


priority = 50