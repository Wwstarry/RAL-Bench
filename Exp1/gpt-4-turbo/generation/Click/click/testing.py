import sys
import io
import os
import contextlib

class Result:
    def __init__(self, exit_code, output, exception=None):
        self.exit_code = exit_code
        self.output = output
        self.exception = exception

    def __str__(self):
        return self.output

class CliRunner:
    def __init__(self, env=None):
        self.env = env or {}

    def invoke(self, cli, args=None, input=None, env=None, catch_exceptions=True):
        args = args or []
        env = env or {}
        output = io.StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_stdin = sys.stdin
        old_env = os.environ.copy()
        exit_code = 0
        exception = None
        try:
            sys.stdout = output
            sys.stderr = output
            if input is not None:
                sys.stdin = io.StringIO(input)
            os.environ.update(self.env)
            os.environ.update(env)
            try:
                rv = cli.main(args=args, standalone_mode=True)
            except SystemExit as e:
                exit_code = e.code if isinstance(e.code, int) else 1
            except Exception as e:
                exception = e
                if not catch_exceptions:
                    raise
                exit_code = 1
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            sys.stdin = old_stdin
            os.environ.clear()
            os.environ.update(old_env)
        return Result(exit_code, output.getvalue(), exception)