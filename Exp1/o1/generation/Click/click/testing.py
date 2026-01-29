# click/testing.py
# Implementation of CliRunner for testing Click commands.

import os
import sys
import io
from contextlib import contextmanager

class Result:
    """
    Holds the captured results of invoking a CLI command.
    """
    def __init__(self, runner, output, exit_code, exception=None):
        self.runner = runner
        self.output = output
        self.exit_code = exit_code
        self.exception = exception

    @property
    def stdout(self):
        return self.output


class CliRunner:
    """
    Provides functionality to invoke commands and capture outputs,
    exit codes, and exceptions for testing.
    """
    def __init__(self):
        pass

    @contextmanager
    def isolation(self, input=None, env=None):
        old_stdin = sys.stdin
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        old_env = os.environ.copy()

        try:
            if input is not None:
                sys.stdin = io.StringIO(input)
            else:
                sys.stdin = io.StringIO()

            outbuf = io.StringIO()
            errbuf = io.StringIO()
            sys.stdout = outbuf
            sys.stderr = errbuf

            if env:
                os.environ.update(env)

            yield outbuf, errbuf
        finally:
            sys.stdin = old_stdin
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            os.environ.clear()
            os.environ.update(old_env)

    def invoke(self, cli, args=None, input=None, env=None, catch_exceptions=True):
        """
        Invoke a command, capturing the output, exit code, and exception.
        """
        if args is None:
            args = []
        with self.isolation(input=input, env=env) as (outbuf, errbuf):
            exc = None
            exit_code = 0
            try:
                # If it's a group or command, call main()
                cli.main(args=args)
            except SystemExit as e:
                # handle sys.exit()
                exit_code = e.code if isinstance(e.code, int) else 1
            except Exception as e:
                if not catch_exceptions:
                    raise
                exc = e
                exit_code = 1
            output = outbuf.getvalue() + errbuf.getvalue()
        return Result(self, output, exit_code, exc)