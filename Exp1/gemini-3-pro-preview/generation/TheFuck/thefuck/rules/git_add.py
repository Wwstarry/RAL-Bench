# Rule: git add
# Detects: Changes not staged for commit

def match(command):
    return ('git' in command.script_parts and
            'commit' in command.script_parts and
            'Changes not staged for commit' in command.stdout)

def get_new_command(command):
    return 'git add . && ' + command.script