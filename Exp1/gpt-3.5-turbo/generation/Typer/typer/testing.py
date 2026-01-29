import sys
import io
import contextlib
import typing
import subprocess

class Result:
    def __init__(self, exit_code: int, output: str, exception: Exception = None):
        self.exit_code = exit_code
        self.output = output
        self.exception = exception

class CliRunner:
    def __init__(self):
        pass

    def invoke(self, app, args=None, input=None):
        # app is a Typer instance or a callable
        # args is list of strings or None
        # input is string or None (not used here)
        if args is None:
            args = []
        output = io.StringIO()
        exc = None
        exit_code = 0
        # Save original sys.argv and sys.stdout/stderr
        orig_argv = sys.argv
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        sys.argv = [orig_argv[0] if orig_argv else "app"] + args
        sys.stdout = output
        sys.stderr = output
        try:
            app(args)
        except SystemExit as e:
            exit_code = e.code if isinstance(e.code, int) else 1
        except Exception as e:
            exc = e
            exit_code = 1
        finally:
            sys.argv = orig_argv
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr
        return Result(exit_code=exit_code, output=output.getvalue(), exception=exc)