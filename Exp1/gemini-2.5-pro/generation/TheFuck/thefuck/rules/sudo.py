enabled_by_default = True
priority = 100  # High priority because it's a common mistake

def match(command):
    return 'permission denied' in command.stderr.lower()

def get_new_command(command):
    return 'sudo {}'.format(command.script)