"""Rule for correcting git push commands."""

from thefuck.command import Command


def match(command: Command) -> bool:
    """Check if this rule applies to the command."""
    if not command.script.startswith("git push"):
        return False
    
    # Check for common git push errors
    return "rejected" in command.stderr or "no changes added" in command.stderr


def get_corrected(command: Command):
    """Return corrected command(s)."""
    return []