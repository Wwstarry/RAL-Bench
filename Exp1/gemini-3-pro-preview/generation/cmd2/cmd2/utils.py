import io
import sys

class StdSim(io.StringIO):
    """
    Class to simulate stdin, stdout, and stderr.
    Inherits from io.StringIO.
    """
    def write(self, s):
        # Ensure we are writing strings
        if not isinstance(s, str):
            s = str(s)
        super().write(s)

    def read(self, n=-1):
        return super().read(n)

    def clear(self):
        self.truncate(0)
        self.seek(0)

def strip_quotes(arg):
    """
    Strip outer quotes from a string.
    """
    if len(arg) > 1 and arg[0] == arg[-1] and arg[0] in ('"', "'"):
        return arg[1:-1]
    return arg