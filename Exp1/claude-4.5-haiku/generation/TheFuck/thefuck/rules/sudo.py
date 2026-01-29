"""Rule for adding sudo to commands that need it."""

from thefuck.command import Command


def match(command: Command) -> bool:
    """Check if this rule applies to the command."""
    if command.script.startswith("sudo "):
        return False
    
    # Check for permission denied errors
    return "permission denied" in command.stderr.lower() or "permission denied" in command.stdout.lower()


def get_corrected(command: Command):
    """Return corrected command(s)."""
    corrected = f"sudo {command.script}"
    return [corrected]