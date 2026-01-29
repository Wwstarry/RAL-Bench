"""Rule for git checkout errors."""


def match(command):
    """Match git checkout errors."""
    if not command.script.startswith('git checkout'):
        return False
    
    return ('did not match any file(s) known to git' in command.output or
            'pathspec' in command.output.lower())


def get_new_command(command):
    """Suggest git checkout -b for new branches."""
    parts = command.script.split()
    if len(parts) >= 3:
        # Suggest creating a new branch
        branch_name = parts[2]
        return f'git checkout -b {branch_name}'
    
    return command.script


priority = 100