import sys
import io

class OutputCapture:
    """Context manager to capture output from Cmd2 poutput/perror."""

    def __init__(self, cmd2_instance):
        self.cmd2_instance = cmd2_instance
        self._stdout = None
        self._stderr = None
        self.stdout_buffer = io.StringIO()
        self.stderr_buffer = io.StringIO()

    def __enter__(self):
        self._stdout = self.cmd2_instance.stdout
        self._stderr = sys.stderr
        self.cmd2_instance.stdout = self.stdout_buffer
        sys.stderr = self.stderr_buffer
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cmd2_instance.stdout = self._stdout
        sys.stderr = self._stderr

    def get_output(self):
        return self.stdout_buffer.getvalue()

    def get_error(self):
        return self.stderr_buffer.getvalue()