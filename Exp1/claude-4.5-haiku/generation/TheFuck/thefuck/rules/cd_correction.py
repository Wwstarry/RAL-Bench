"""Rule for correcting cd command typos."""

from thefuck.command import Command


def match(command: Command) -> bool:
    """Check if this rule applies to the command."""
    if not command.script.startswith("cd "):
        return False
    
    # Check if cd failed
    if command.returncode == 0:
        return False
    
    return "No such file or directory" in command.stderr or "cannot access" in command.stderr


def get_corrected(command: Command):
    """Return corrected command(s)."""
    # For now, just return empty list
    return []