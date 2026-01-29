"""
Testing utilities for Click commands.
"""

import sys
import os
from io import StringIO
from typing import Any, Dict, List, Optional, Union
from click.core import Command, Group, Context


class Result:
    """Result of a CLI invocation."""
    
    def __init__(
        self,
        output: str = "",
        exit_code: int = 0,
        exception: Optional[Exception] = None,
        exc_info: Optional[tuple] = None,
    ):
        self.output = output
        self.exit_code = exit_code
        self.exception = exception
        self.exc_info = exc_info
    
    def __repr__(self) -> str:
        return f"<Result exit_code={self.exit_code}>"


class CliRunner:
    """Test runner for Click commands."""
    
    def __init__(
        self,
        mix_stderr: bool = True,
        env: Optional[Dict[str, str]] = None,
    ):
        self.mix_stderr = mix_stderr
        self.env = env or {}
    
    def invoke(
        self,
        cli: Union[Command, Group],
        args: Optional[Union[str, List[str]]] = None,
        input: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        catch_exceptions: bool = True,
        color: bool = False,
        **extra
    ) -> Result:
        """Invoke a CLI command and return the result."""
        
        # Parse args
        if args is None:
            args = []
        elif isinstance(args, str):
            args = args.split()
        else:
            args = list(args)
        
        # Merge environment
        merged_env = dict(self.env)
        if env:
            merged_env.update(env)
        
        # Capture output
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_stdin = sys.stdin
        old_env = dict(os.environ)
        
        stdout = StringIO()
        stderr = StringIO() if not self.mix_stderr else stdout
        
        if input is not None:
            stdin = StringIO(input)
        else:
            stdin = StringIO()
        
        exit_code = 0
        exception = None
        exc_info = None
        
        try:
            # Set up environment
            sys.stdout = stdout
            sys.stderr = stderr
            sys.stdin = stdin
            
            for key, value in merged_env.items():
                os.environ[key] = value
            
            # Invoke command
            try:
                result = cli.main(args=args, standalone_mode=False, **extra)
                if isinstance(result, int):
                    exit_code = result
            except SystemExit as e:
                exit_code = e.code if e.code is not None else 0
                if catch_exceptions:
                    exception = e
                    exc_info = sys.exc_info()
                else:
                    raise
            except Exception as e:
                exit_code = 1
                exception = e
                exc_info = sys.exc_info()
                if not catch_exceptions:
                    raise
        
        finally:
            # Restore environment
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            sys.stdin = old_stdin
            
            for key in list(os.environ.keys()):
                if key not in old_env:
                    del os.environ[key]
            for key, value in old_env.items():
                os.environ[key] = value
        
        output = stdout.getvalue()
        
        return Result(
            output=output,
            exit_code=exit_code,
            exception=exception,
            exc_info=exc_info,
        )