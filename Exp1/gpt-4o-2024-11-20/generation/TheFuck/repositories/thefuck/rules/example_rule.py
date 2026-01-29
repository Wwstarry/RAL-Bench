def match(command):
    """Example rule: Match if the command contains 'teh'."""
    return "teh" in command.script


def get_new_command(command):
    """Example rule: Replace 'teh' with 'the'."""
    return command.script.replace("teh", "the")