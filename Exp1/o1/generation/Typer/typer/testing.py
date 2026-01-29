import sys
import io
from contextlib import redirect_stdout, redirect_stderr

class CliRunner:
    """
    A simple test runner to invoke Typer CLI apps and capture output.
    Usage:
        runner = CliRunner()
        result = runner.invoke(app, ["cmd", "arg"])
        assert result.exit_code == 0
        assert "expected output" in result.output
    """

    def invoke(self, app, args=None):
        if args is None:
            args = []

        # We'll capture output by redirecting stdout/stderr
        stdout_buffer = io.StringIO()
        stderr_buffer = io.StringIO()
        exit_code = 0

        # Save original sys.argv
        original_argv = sys.argv
        sys.argv = [original_argv[0]] + args

        try:
            with redirect_stdout(stdout_buffer), redirect_stderr(stderr_buffer):
                try:
                    app()
                except SystemExit as e:
                    exit_code = e.code if e.code else 0
        finally:
            sys.argv = original_argv

        return InvokeResult(
            exit_code=exit_code,
            stdout=stdout_buffer.getvalue(),
            stderr=stderr_buffer.getvalue(),
        )


class InvokeResult:
    """Holds the result of a command invocation via CliRunner."""

    def __init__(self, exit_code, stdout, stderr):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

    @property
    def output(self):
        # For compatibility with some test patterns that use 'output' property.
        return self.stdout