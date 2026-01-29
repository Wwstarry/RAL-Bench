"""Rule for docker command typos."""


def match(command):
    """Match docker command errors."""
    if not command.script.startswith('docker '):
        return False
    
    return ('is not a docker command' in command.output.lower() or
            'unknown command' in command.output.lower())


def get_new_command(command):
    """Suggest correct docker commands."""
    typo_map = {
        'pul': 'pull',
        'pus': 'push',
        'buil': 'build',
        'rnu': 'run',
        'psuh': 'push',
    }
    
    parts = command.script.split()
    if len(parts) >= 2:
        cmd = parts[1]
        if cmd in typo_map:
            parts[1] = typo_map[cmd]
            return ' '.join(parts)
    
    return command.script


priority = 100