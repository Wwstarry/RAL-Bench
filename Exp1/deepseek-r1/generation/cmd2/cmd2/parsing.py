import shlex

class Statement:
    """Represents a parsed command statement."""
    def __init__(self, raw):
        self.raw = raw
        self.args = []
        self.parse()

    def parse(self):
        """Tokenize raw command input."""
        if self.raw.strip():
            self.args = shlex.split(self.raw)

    def __repr__(self):
        return f"Statement(raw={self.raw!r}, args={self.args})"

def parse_arguments(arg_string):
    """Parse argument string into tokens."""
    return shlex.split(arg_string) if arg_string else []