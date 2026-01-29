def select_command(corrected_commands):
    """
    Returns the selected command.

    In a real implementation, this would be an interactive prompt.
    For testing purposes, this is non-interactive and deterministic,
    always selecting the first (highest priority) command.

    :type corrected_commands: list[thefuck.types.CorrectedCommand]
    :rtype: thefuck.types.CorrectedCommand or None
    """
    if corrected_commands:
        return corrected_commands[0]
    return None