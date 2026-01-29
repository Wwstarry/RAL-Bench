"""Rule for cp omitting directory."""


def match(command):
    """Match cp errors for directories."""
    if not command.script.startswith('cp '):
        return False
    
    return ('omitting directory' in command.output.lower() and
            '-r' not in command.script)


def get_new_command(command):
    """Add -r flag to cp."""
    parts = command.script.split()
    if len(parts) >= 3:
        return f'cp -r {" ".join(parts[1:])}'
    
    return command.script


priority = 100