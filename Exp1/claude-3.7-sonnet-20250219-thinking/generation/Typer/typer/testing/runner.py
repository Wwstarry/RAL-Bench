import io
import sys
from typing import Any, Dict, List, Optional, Union

class Result:
    """Result of invoking a CLI application."""
    
    def __init__(
        self,
        runner,
        stdout_bytes,
        stderr_bytes,
        exit_code,
    ):
        self.runner = runner
        self.exit_code = exit_code
        self.stdout_bytes = stdout_bytes
        self.stderr_bytes = stderr_bytes
        self.stdout = stdout_bytes.getvalue() if stdout_bytes else ""
        self.stderr = stderr_bytes.getvalue() if stderr_bytes else ""
    
    def __repr__(self):
        return f"<Result {self.exit_code}>"

class CliRunner:
    """Helper class to test CLI applications."""
    
    def __init__(
        self,
        mix_stderr: bool = False,
    ):
        self.mix_stderr = mix_stderr
    
    def invoke(
        self,
        cli: Any,
        args: Optional[Union[str, List[str]]] = None,
        input: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        catch_exceptions: bool = True,
        color: bool = False,
    ):
        """Invoke a CLI application with the given arguments."""
        old_argv = sys.argv.copy()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        stdout_bytes = io.StringIO()
        stderr_bytes = stdout_bytes if self.mix_stderr else io.StringIO()
        
        sys.stdout = stdout_bytes
        sys.stderr = stderr_bytes
        
        if args is None:
            args = []
        elif isinstance(args, str):
            args = args.split()
        
        sys.argv = ["cli"] + args
        
        try:
            exit_code = cli()
            if exit_code is None:
                exit_code = 0
        except Exception as e:
            if catch_exceptions:
                import traceback
                traceback.print_exc(file=stderr_bytes)
                exit_code = 1
            else:
                sys.argv = old_argv
                sys.stdout = old_stdout
                sys.stderr = old_stderr
                raise
        finally:
            sys.argv = old_argv
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        return Result(
            runner=self,
            stdout_bytes=stdout_bytes,
            stderr_bytes=None if self.mix_stderr else stderr_bytes,
            exit_code=exit_code,
        )