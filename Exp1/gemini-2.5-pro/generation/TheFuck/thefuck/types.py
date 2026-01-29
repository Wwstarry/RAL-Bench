from collections import namedtuple

_Command = namedtuple('Command', ('script', 'script_parts', 'stdout', 'stderr'))
_CorrectedCommand = namedtuple('CorrectedCommand', ('script', 'side_effect', 'priority'))

class Command(_Command):
    """
    Represents a failed command.
    """
    def __repr__(self):
        return f"Command(script={self.script!r}, stdout={self.stdout!r}, stderr={self.stderr!r})"

class CorrectedCommand(_CorrectedCommand):
    """
    Represents a corrected command suggestion.
    """
    def __repr__(self):
        return f"CorrectedCommand(script={self.script!r}, priority={self.priority})"

    def __eq__(self, other):
        return self.script == other.script

    def __hash__(self):
        return hash(self.script)

def new_command(script, stdout, stderr):
    """
    Factory function for creating Command objects.
    """
    return Command(script, script.split(), stdout, stderr)