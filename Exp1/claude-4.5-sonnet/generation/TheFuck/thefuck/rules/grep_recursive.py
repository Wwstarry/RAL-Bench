"""Rule for grep on directories."""


def match(command):
    """Match grep errors on directories."""
    if not command.script.startswith('grep '):
        return False
    
    return ('Is a directory' in command.output and
            '-r' not in command.script and
            '-R' not in command.script)


def get_new_command(command):
    """Add -r flag to grep."""
    parts = command.script.split()
    if len(parts) >= 2:
        return f'grep -r {" ".join(parts[1:])}'
    
    return command.script


priority = 100