def match(command):
    """Match if the command indicates a missing argument."""
    return "missing argument" in command.stderr


def get_new_command(command):
    """Suggest adding a placeholder argument."""
    return command.script + " <arg>"