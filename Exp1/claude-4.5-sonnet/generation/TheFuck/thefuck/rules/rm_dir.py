"""Rule for rm on directories."""


def match(command):
    """Match rm errors on directories."""
    if not command.script.startswith('rm '):
        return False
    
    return ('is a directory' in command.output.lower() and
            '-r' not in command.script)


def get_new_command(command):
    """Add -r flag to rm."""
    parts = command.script.split()
    if len(parts) >= 2:
        return f'rm -r {" ".join(parts[1:])}'
    
    return command.script


priority = 100