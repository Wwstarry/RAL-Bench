"""Rule for Python command errors."""


def match(command):
    """Match Python command errors."""
    if not command.script.startswith('python'):
        return False
    
    return ('No module named' in command.output or
            'can\'t open file' in command.output or
            'No such file or directory' in command.output)


def get_new_command(command):
    """Suggest corrections for Python commands."""
    # If trying to run a module, suggest -m flag
    if 'No module named' in command.output:
        parts = command.script.split()
        if len(parts) >= 2 and not '-m' in parts:
            # Insert -m before the module name
            return f'{parts[0]} -m {" ".join(parts[1:])}'
    
    return command.script


priority = 100