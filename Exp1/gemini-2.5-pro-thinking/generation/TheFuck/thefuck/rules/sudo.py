def match(command):
    return 'permission denied' in command.stderr.lower()

def get_new_command(command):
    if command.script.startswith('sudo '):
        return []
    return 'sudo ' + command.script