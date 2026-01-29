def match(command):
    return ('apt-get' in command.script and
            ('permission denied' in command.stderr.lower() or
             'are you root?' in command.stderr.lower()))

def get_new_command(command):
    if command.script.startswith('sudo '):
        return []
    return 'sudo ' + command.script

# Higher priority (lower number) than the generic sudo rule.
priority = 100