# -*- coding: utf-8 -*-

import sys
import os
import shutil
import tempfile
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from io import StringIO

class Result:
    """Holds the captured result of a CLI invocation."""
    def __init__(self, exit_code, stdout, stderr, exception, exc_info=None):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr
        self.exception = exception
        self.exc_info = exc_info

    @property
    def output(self):
        return self.stdout

    def __repr__(self):
        return f"<Result exit_code={self.exit_code} exception={self.exception!r}>"

class CliRunner:
    """A class for testing Click command line interfaces."""
    def __init__(self, charset='utf-8', env=None, echo_stdin=False):
        self.charset = charset
        self.env = env or {}
        self.echo_stdin = echo_stdin

    @contextmanager
    def isolated_filesystem(self):
        """A context manager that creates a temporary folder and changes
        the current working directory to it.
        """
        cwd = os.getcwd()
        d = tempfile.mkdtemp()
        os.chdir(d)
        try:
            yield d
        finally:
            os.chdir(cwd)
            try:
                shutil.rmtree(d)
            except OSError:
                pass

    def invoke(self, cli, args=None, input=None, env=None, catch_exceptions=True):
        """Invokes a command in an isolated environment."""
        exc_info = None
        exception = None
        exit_code = 0

        # Backup system state
        original_argv = sys.argv
        original_stdin = sys.stdin
        original_env = os.environ.copy()

        # Setup new state
        prog_name = cli.name or 'root'
        sys.argv = [prog_name] + (args or [])
        
        if input:
            if isinstance(input, bytes):
                input = input.decode(self.charset)
            sys.stdin = StringIO(str(input))
        else:
            sys.stdin = StringIO()

        # Environment
        test_env = self.env.copy()
        if env:
            test_env.update(env)
        os.environ.clear()
        os.environ.update(test_env)

        stdout_io = StringIO()
        stderr_io = StringIO()

        try:
            with redirect_stdout(stdout_io), redirect_stderr(stderr_io):
                cli.main(args=args, prog_name=prog_name, standalone_mode=False)
        except SystemExit as e:
            exit_code = e.code if isinstance(e.code, int) else 1
            exc_info = sys.exc_info()
        except Exception as e:
            if not catch_exceptions:
                raise
            exception = e
            exc_info = sys.exc_info()
            exit_code = 1
        finally:
            # Restore system state
            sys.argv = original_argv
            sys.stdin = original_stdin
            os.environ.clear()
            os.environ.update(original_env)

        stdout = stdout_io.getvalue()
        stderr = stderr_io.getvalue()

        return Result(
            exit_code=exit_code,
            stdout=stdout,
            stderr=stderr,
            exception=exception,
            exc_info=exc_info,
        )