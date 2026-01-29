import sys
import subprocess
import types
import io
import contextlib

class Result:
    def __init__(self, exit_code, stdout, stderr):
        self.exit_code = exit_code
        self.stdout = stdout
        self.stderr = stderr

class CliRunner:
    def __init__(self):
        pass

    def invoke(self, app, args=None, input=None, catch_exceptions=True):
        args = args or []
        stdout = io.StringIO()
        stderr = io.StringIO()
        exit_code = 0
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        orig_stdin = sys.stdin
        if input is not None:
            sys.stdin = io.StringIO(input)
        try:
            sys.stdout = stdout
            sys.stderr = stderr
            try:
                app_args = list(args)
                app._main(app_args)
            except SystemExit as e:
                exit_code = e.code if isinstance(e.code, int) else 1
            except Exception as e:
                if catch_exceptions:
                    exit_code = 1
                else:
                    raise
        finally:
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr
            sys.stdin = orig_stdin
        return Result(exit_code, stdout.getvalue(), stderr.getvalue())