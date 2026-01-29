"""Rule for permission denied errors."""


def match(command):
    """Match permission denied errors."""
    if command.script.startswith('sudo'):
        return False
    
    return ('permission denied' in command.output.lower() or
            'access denied' in command.output.lower() or
            'operation not permitted' in command.output.lower())


def get_new_command(command):
    """Prepend sudo to the command."""
    return f'sudo {command.script}'


priority = 100