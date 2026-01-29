"""Rule for mkdir without -p flag."""


def match(command):
    """Match mkdir errors for nested directories."""
    if not command.script.startswith('mkdir'):
        return False
    
    return ('No such file or directory' in command.output and
            '-p' not in command.script)


def get_new_command(command):
    """Add -p flag to mkdir."""
    parts = command.script.split()
    if len(parts) >= 2:
        return f'mkdir -p {" ".join(parts[1:])}'
    
    return command.script


priority = 100