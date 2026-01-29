"""Rule for npm run script errors."""


def match(command):
    """Match npm run script errors."""
    if not command.script.startswith('npm '):
        return False
    
    return ('missing script' in command.output.lower() or
            'script not found' in command.output.lower())


def get_new_command(command):
    """Suggest npm run for scripts."""
    parts = command.script.split()
    if len(parts) >= 2 and parts[1] != 'run':
        # Insert 'run' after 'npm'
        return f'npm run {" ".join(parts[1:])}'
    
    return command.script


priority = 100