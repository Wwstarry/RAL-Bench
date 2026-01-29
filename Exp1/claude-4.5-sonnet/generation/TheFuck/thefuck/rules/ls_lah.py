"""Rule for ls -lah typo."""


def match(command):
    """Match ls -lah typo."""
    return command.script == 'ls -lha'


def get_new_command(command):
    """Correct to ls -lah."""
    return 'ls -lah'


priority = 50