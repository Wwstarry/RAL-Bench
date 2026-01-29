# cmd2/utils.py

"""
Utility functions for Cmd2.
"""

import contextlib
import io


@contextlib.contextmanager
def capture_output():
    """
    Context manager to capture stdout and stderr output.
    """
    new_out, new_err = io.StringIO(), io.StringIO()
    old_out, old_err = io.sys.stdout, io.sys.stderr
    try:
        io.sys.stdout, io.sys.stderr = new_out, new_err
        yield new_out, new_err
    finally:
        io.sys.stdout, io.sys.stderr = old_out, old_err


class TranscriptTester:
    """
    A simple transcript-based testing utility.
    """

    def __init__(self, cmd_instance):
        self.cmd_instance = cmd_instance

    def run_transcript(self, transcript_file):
        """
        Run commands from a transcript file and compare output.
        """
        with open(transcript_file, "r") as file:
            for line in file:
                command, expected_output = line.strip().split("=>")
                with capture_output() as (out, _):
                    self.cmd_instance.onecmd(command.strip())
                actual_output = out.getvalue().strip()
                if actual_output != expected_output.strip():
                    raise AssertionError(
                        f"Transcript test failed for command '{command}': "
                        f"expected '{expected_output.strip()}', got '{actual_output}'"
                    )