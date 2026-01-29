def match(command):
    """Match if the command starts with an unknown command."""
    return "command not found" in command.stderr


def get_new_command(command):
    """Suggest a corrected command."""
    parts = command.script.split()
    if not parts:
        return command.script
    corrected_command = parts[0] + " --help"
    return corrected_command