"""Rule for apt-get typos."""


def match(command):
    """Match apt-get typos."""
    return (command.script.startswith('apt-get') and
            ('Invalid operation' in command.output or
             'E: Invalid operation' in command.output))


def get_new_command(command):
    """Correct apt-get typos."""
    # Common typos
    typo_map = {
        'isntall': 'install',
        'intall': 'install',
        'instal': 'install',
        'udpate': 'update',
        'upate': 'update',
    }
    
    parts = command.script.split()
    if len(parts) >= 2:
        operation = parts[1]
        if operation in typo_map:
            parts[1] = typo_map[operation]
            return ' '.join(parts)
    
    return command.script


priority = 100