import sys
import traceback
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr
from typing import List, Optional, Any, Sequence

class Result:
    """
    The result of a CLI invocation for testing.
    """
    def __init__(
        self,
        stdout: str,
        stderr: str,
        exit_code: int,
        exception: Optional[BaseException],
    ):
        self.stdout = stdout
        self.stderr = stderr
        self.exit_code = exit_code
        self.exception = exception

    @property
    def stdout_bytes(self) -> bytes:
        return self.stdout.encode("utf-8")

    @property
    def stderr_bytes(self) -> bytes:
        return self.stderr.encode("utf-8")

    def __repr__(self) -> str:
        return f"<Result exit_code={self.exit_code}>"

class CliRunner:
    """
    A helper for invoking and testing Typer applications.
    """
    def invoke(
        self,
        app: Any,
        args: Optional[Sequence[str]] = None,
    ) -> Result:
        exit_code = 0
        exception: Optional[BaseException] = None
        
        stdout_io = StringIO()
        stderr_io = StringIO()

        try:
            with redirect_stdout(stdout_io), redirect_stderr(stderr_io):
                app(args=list(args) if args is not None else [], prog_name="cli.py")
        except SystemExit as e:
            if isinstance(e.code, int):
                exit_code = e.code
            elif e.code is None:
                exit_code = 0
            else:
                exit_code = 1
            exception = e
        except Exception as e:
            exit_code = 1
            exception = e
            traceback.print_exc(file=stderr_io)
        
        stdout = stdout_io.getvalue()
        stderr = stderr_io.getvalue()
        
        return Result(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            exception=exception,
        )