import shlex
from .const import DEFAULT_PRIORITY

class Command(object):
    """Represents a failed command."""
    def __init__(self, script, stdout, stderr):
        self.script = script
        self.stdout = stdout
        self.stderr = stderr
        try:
            self.script_parts = shlex.split(script)
        except ValueError:
            self.script_parts = script.split()

    def __repr__(self):
        return 'Command(script={}, stdout={}, stderr={})'.format(
            self.script, self.stdout, self.stderr)

class CorrectedCommand(object):
    """Represents a corrected command suggestion."""
    def __init__(self, script, side_effect=None, priority=DEFAULT_PRIORITY):
        self.script = script
        self.side_effect = side_effect
        self.priority = priority

    def __eq__(self, other):
        if isinstance(other, CorrectedCommand):
            return self.script == other.script
        return False

    def __hash__(self):
        return hash(self.script)

    def __repr__(self):
        return 'CorrectedCommand(script={}, priority={})'.format(
            self.script, self.priority)