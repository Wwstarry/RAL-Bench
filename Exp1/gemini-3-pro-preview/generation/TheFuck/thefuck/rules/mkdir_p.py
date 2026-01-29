# Rule: mkdir -p
# Detects: mkdir: cannot create directory '...': No such file or directory

def match(command):
    return 'mkdir' in command.script_parts and 'No such file or directory' in command.stderr

def get_new_command(command):
    return command.script.replace('mkdir', 'mkdir -p')