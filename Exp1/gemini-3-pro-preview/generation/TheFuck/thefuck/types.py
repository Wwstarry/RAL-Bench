class Command(object):
    def __init__(self, script, stdout, stderr):
        self.script = script
        self.stdout = stdout
        self.stderr = stderr

    @property
    def script_parts(self):
        return self.script.split()

    def __eq__(self, other):
        if isinstance(other, Command):
            return (self.script, self.stdout, self.stderr) == (other.script, other.stdout, other.stderr)
        return False

    def __repr__(self):
        return 'Command(script={}, stdout={}, stderr={})'.format(
            self.script, self.stdout, self.stderr)


class CorrectedCommand(object):
    def __init__(self, script, side_effect=None, priority=1000):
        self.script = script
        self.side_effect = side_effect
        self.priority = priority

    def __eq__(self, other):
        if isinstance(other, CorrectedCommand):
            return (self.script, self.side_effect) == (other.script, other.side_effect)
        return False

    def __hash__(self):
        return hash((self.script, self.side_effect))

    def __repr__(self):
        return 'CorrectedCommand(script={}, side_effect={}, priority={})'.format(
            self.script, self.side_effect, self.priority)