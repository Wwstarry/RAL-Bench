# click/testing.py

import sys
import os
import traceback
from io import StringIO, BytesIO
from contextlib import contextmanager

class Result:
    """Holds the captured result of a CLI invocation."""
    def __init__(self, runner, stdout_bytes, stderr_bytes, exit_code, exception, traceback_string=None):
        self.runner = runner
        self.stdout_bytes = stdout_bytes
        self.stderr_bytes = stderr_bytes
        self.exit_code = exit_code
        self.exception = exception
        self.traceback = traceback_string

    @property
    def output(self):
        return self.stdout

    @property
    def stdout(self):
        return self.stdout_bytes.decode(self.runner.charset, "replace").replace("\r\n", "\n")

    @property
    def stderr(self):
        return self.stderr_bytes.decode(self.runner.charset, "replace").replace("\r\n", "\n")

    def __repr__(self):
        return f"<Result exit_code={self.exit_code}>"

class CliRunner:
    """A tool for testing Click command-line interfaces."""
    def __init__(self, charset="utf-8", env=None):
        self.charset = charset
        self.env = env or {}

    @contextmanager
    def isolation(self, input=None, env=None, color=False):
        """Isolates the environment for a test run."""
        old_stdout, old_stderr = sys.stdout, sys.stderr
        
        stdout_buffer = StringIO()
        stderr_buffer = StringIO()
        
        sys.stdout, sys.stderr = stdout_buffer, stderr_buffer
        
        old_env = os.environ.copy()
        if self.env:
            os.environ.update(self.env)
        if env:
            os.environ.update(env)
        
        try:
            yield (stdout_buffer, stderr_buffer)
        finally:
            sys.stdout, sys.stderr = old_stdout, old_stderr
            os.environ.clear()
            os.environ.update(old_env)

    def invoke(self, cli, args=None, input=None, env=None, catch_exceptions=True, **extra):
        """Invokes a command for testing."""
        if args is None:
            args = []
        elif isinstance(args, str):
            # A simple shlex replacement for basic cases
            import shlex
            args = shlex.split(args)
            
        exc_info = None
        exit_code = 0
        
        command = getattr(cli, '__click_command__', None)
        if command is None:
            raise TypeError("'cli' is not a Click command.")

        with self.isolation(input=input, env=env) as (stdout, stderr):
            try:
                command.main(args=args, prog_name=command.name or 'root', standalone_mode=False, **extra)
            except SystemExit as e:
                exit_code = e.code if e.code is not None else 0
            except Exception as e:
                if not catch_exceptions:
                    raise
                exc_info = sys.exc_info()
                exit_code = 1
            
            stdout_bytes = stdout.getvalue().encode(self.charset)
            stderr_bytes = stderr.getvalue().encode(self.charset)
            
            exception = exc_info[1] if exc_info else None
            traceback_str = None
            if exc_info:
                traceback_str = "".join(traceback.format_exception(*exc_info))

        return Result(
            runner=self,
            stdout_bytes=stdout_bytes,
            stderr_bytes=stderr_bytes,
            exit_code=exit_code,
            exception=exception,
            traceback_string=traceback_str
        )