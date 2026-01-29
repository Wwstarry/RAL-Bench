"""Rule for git pull errors."""


def match(command):
    """Match git pull errors."""
    if not command.script.startswith('git pull'):
        return False
    
    return ('specify how to reconcile' in command.output or
            'need to specify how to reconcile' in command.output)


def get_new_command(command):
    """Add merge strategy to git pull."""
    return command.script + ' --rebase'


priority = 100