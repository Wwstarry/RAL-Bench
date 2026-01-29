"""Rule for git push --set-upstream."""


def match(command):
    """Match git push errors that need --set-upstream."""
    if not command.script.startswith('git push'):
        return False
    
    return ('--set-upstream' in command.output or
            'set-upstream' in command.output or
            'has no upstream branch' in command.output)


def get_new_command(command):
    """Add --set-upstream to git push."""
    # Extract branch name from output if present
    output_lines = command.output.split('\n')
    
    for line in output_lines:
        if 'git push --set-upstream' in line:
            # Extract the suggested command
            start = line.find('git push --set-upstream')
            if start >= 0:
                return line[start:].strip()
    
    # Fallback: add --set-upstream origin <current-branch>
    parts = command.script.split()
    if len(parts) >= 2:
        return f'{command.script} --set-upstream origin master'
    
    return command.script + ' --set-upstream origin master'


priority = 100