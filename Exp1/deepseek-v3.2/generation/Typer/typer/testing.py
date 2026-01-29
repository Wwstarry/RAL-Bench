"""
Testing utilities for Typer.
"""
import sys
from io import StringIO
from typing import Optional
from .core import Typer, Exit


class CliRunner:
    """Test runner for Typer applications."""
    
    def __init__(self):
        pass
    
    def invoke(
        self,
        app: Typer,
        args: Optional[list] = None,
        input: Optional[str] = None,
        catch_exceptions: bool = True,
    ) -> "Result":
        """Invoke a Typer application with given arguments."""
        if args is None:
            args = []
        
        # Capture stdout and stderr
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_stdin = sys.stdin
        
        stdout = StringIO()
        stderr = StringIO()
        
        if input is not None:
            stdin = StringIO(input)
        else:
            stdin = StringIO()
        
        exit_code = 0
        exception = None
        
        try:
            sys.stdout = stdout
            sys.stderr = stderr
            sys.stdin = stdin
            
            app.run(*args)
        except Exit as e:
            exit_code = e.code
        except SystemExit as e:
            if isinstance(e.code, int):
                exit_code = e.code
            else:
                exit_code = 1
        except Exception as e:
            if catch_exceptions:
                exception = e
                stderr.write(str(e))
            else:
                raise
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            sys.stdin = old_stdin
        
        return Result(
            exit_code=exit_code,
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
            exception=exception,
        )


class Result:
    """Result of a CLI invocation."""
    
    def __init__(
        self,
        exit_code: int,
        stdout: str,
        stderr: str,
        exception: Optional[Exception] = None,
    ):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.exception = exception
    
    @property
    def output(self) -> str:
        """Get combined stdout and stderr."""
        return self.stdout + self.stderr