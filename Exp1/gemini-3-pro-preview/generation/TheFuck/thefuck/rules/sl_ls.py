# Rule: sl -> ls
# Detects: command not found: sl (or user typed sl)

def match(command):
    return command.script == 'sl'

def get_new_command(command):
    return 'ls'