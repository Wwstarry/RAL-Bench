import sys
from io import StringIO

class StdSim:
    """Simulate stdout/stderr with capture capability."""
    def __init__(self):
        self.buffer = StringIO()
        self.encoding = sys.stdout.encoding

    def write(self, text):
        """Capture written text."""
        self.buffer.write(text)

    def getvalue(self):
        """Return captured content."""
        return self.buffer.getvalue()

    def reset(self):
        """Clear captured content."""
        self.buffer.seek(0)
        self.buffer.truncate(0)

class OutputRecorder:
    """Record output during command execution."""
    def __init__(self):
        self.original_stdout = None
        self.original_stderr = None
        self.captured = None
        self.simulator = StdSim()

    def start(self):
        """Begin output capturing."""
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr
        sys.stdout = sys.stderr = self.simulator
        self.simulator.reset()

    def stop(self):
        """End capturing and return output."""
        sys.stdout = self.original_stdout
        sys.stderr = self.original_stderr
        self.captured = self.simulator.getvalue()
        return self.captured

class TranscriptCapture:
    """Manage transcript recording for testing."""
    def __init__(self):
        self.lines = []

    def write(self, text):
        """Append text to transcript."""
        self.lines.append(text)

    def get_transcript(self):
        """Return full transcript content."""
        return ''.join(self.lines)