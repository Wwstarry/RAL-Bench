# Rule: cp -r
# Detects: cp: omitting directory 'dir'
# Suggests: cp -a 'dir'

def match(command):
    return 'cp' in command.script_parts and "omitting directory" in command.stderr

def get_new_command(command):
    return command.script.replace('cp', 'cp -a', 1)