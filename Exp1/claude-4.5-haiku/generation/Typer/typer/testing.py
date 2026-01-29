"""Testing utilities for Typer applications."""

import sys
from io import StringIO
from typing import Any, List, Optional
from .main import Typer


class CliRunner:
    """Test runner for Typer CLI applications."""

    def invoke(
        self,
        app: Typer,
        args: Optional[List[str]] = None,
        input: Optional[str] = None,
        catch_exceptions: bool = True,
    ) -> "Result":
        """Invoke a Typer application and return the result."""
        if args is None:
            args = []

        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_stdin = sys.stdin

        stdout_capture = StringIO()
        stderr_capture = StringIO()

        sys.stdout = stdout_capture
        sys.stderr = stderr_capture

        if input is not None:
            sys.stdin = StringIO(input)

        exit_code = 0
        exception = None

        try:
            result = app.main(args=args, standalone_mode=False)
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0
            if not catch_exceptions:
                raise
        except Exception as e:
            exit_code = 1
            exception = e
            if not catch_exceptions:
                raise
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            sys.stdin = old_stdin

        output = stdout_capture.getvalue()
        stderr_output = stderr_capture.getvalue()

        return Result(
            exit_code=exit_code,
            output=output,
            stderr=stderr_output,
            exception=exception,
        )


class Result:
    """Result of invoking a Typer application."""

    def __init__(
        self,
        exit_code: int,
        output: str,
        stderr: str = "",
        exception: Optional[Exception] = None,
    ):
        self.exit_code = exit_code
        self.output = output
        self.stderr = stderr
        self.exception = exception

    def __repr__(self) -> str:
        return (
            f"Result(exit_code={self.exit_code}, "
            f"output={self.output!r}, "
            f"stderr={self.stderr!r})"
        )