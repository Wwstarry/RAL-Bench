"""Rule to suggest adding sudo to a failed command."""

from thefuck.rules import register
from thefuck.types import Command
from typing import List


@register
def sudo(command: Command) -> List[str]:
    """Suggest adding sudo to a failed command."""
    if (command.return_code != 0 and
        ('permission denied' in command.stderr.lower() or
         'not permitted' in command.stderr.lower() or
         'Operation not permitted' in command.stderr)):
        return [f"sudo {command.script}"]
    return []