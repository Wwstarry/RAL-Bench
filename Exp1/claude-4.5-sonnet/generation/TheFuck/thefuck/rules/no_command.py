"""Rule for command not found errors."""


def match(command):
    """Match command not found errors."""
    return ('command not found' in command.output.lower() or
            'not found' in command.output.lower() or
            'is not recognized' in command.output.lower())


def get_new_command(command):
    """Try to suggest similar commands."""
    script = command.script.strip()
    
    # Common typos
    typo_map = {
        'gti': 'git',
        'got': 'git',
        'gut': 'git',
        'car': 'cat',
        'cta': 'cat',
        'sl': 'ls',
        'grpe': 'grep',
        'gerp': 'grep',
        'pytohn': 'python',
        'pyhton': 'python',
        'dc': 'cd',
    }
    
    parts = script.split()
    if parts:
        cmd = parts[0]
        if cmd in typo_map:
            parts[0] = typo_map[cmd]
            return ' '.join(parts)
    
    return script


priority = 200