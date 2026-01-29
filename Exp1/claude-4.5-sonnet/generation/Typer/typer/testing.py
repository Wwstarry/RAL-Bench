"""Testing utilities for Typer."""

import sys
from io import StringIO
from typing import List, Optional, Any
from .main import Typer


class Result:
    """Result of a CLI invocation."""
    
    def __init__(
        self,
        exit_code: int,
        output: str,
        exception: Optional[Exception] = None
    ):
        self.exit_code = exit_code
        self.output = output
        self.exception = exception
        self.stdout = output


class CliRunner:
    """Test runner for Typer applications."""
    
    def __init__(self, **kwargs: Any):
        self.mix_stderr = kwargs.get("mix_stderr", True)
    
    def invoke(
        self,
        app: Typer,
        args: Optional[List[str]] = None,
        **kwargs: Any
    ) -> Result:
        """Invoke a Typer application with given arguments."""
        if args is None:
            args = []
        
        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        
        sys.stdout = stdout_capture
        if self.mix_stderr:
            sys.stderr = stdout_capture
        else:
            sys.stderr = stderr_capture
        
        exit_code = 0
        exception = None
        
        try:
            exit_code = app._run(args)
        except SystemExit as e:
            exit_code = e.code if e.code is not None else 0
        except Exception as e:
            exception = e
            exit_code = 1
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        output = stdout_capture.getvalue()
        if not self.mix_stderr and stderr_capture.getvalue():
            output += stderr_capture.getvalue()
        
        return Result(
            exit_code=exit_code,
            output=output,
            exception=exception
        )