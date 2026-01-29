import sys
import os
from io import StringIO
from contextlib import contextmanager

class Result:
    def __init__(self, runner, stdout_bytes, stderr_bytes, exit_code, exception, exc_info=None):
        self.runner = runner
        self.stdout_bytes = stdout_bytes
        self.stderr_bytes = stderr_bytes
        self.exit_code = exit_code
        self.exception = exception
        self.exc_info = exc_info

    @property
    def output(self):
        return self.stdout_bytes

    @property
    def stdout(self):
        return self.stdout_bytes

    @property
    def stderr(self):
        return self.stderr_bytes

    def __repr__(self):
        return f"<Result exit_code={self.exit_code} stdout={self.stdout_bytes!r} stderr={self.stderr_bytes!r}>"

class CliRunner:
    def __init__(self, env=None, echo_stdin=False):
        self.env = env or {}
        self.echo_stdin = echo_stdin

    @contextmanager
    def isolation(self, input=None, env=None, color=False):
        env = env or {}
        old_env = {}
        try:
            for key, value in {**self.env, **env}.items():
                old_env[key] = os.environ.get(key)
                os.environ[key] = value
            sys.stdout = StringIO()
            sys.stderr = StringIO()
            if input is not None:
                sys.stdin = StringIO(input)
            yield sys.stdout, sys.stderr
        finally:
            for key, value in old_env.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
            sys.stdin = sys.__stdin__

    def invoke(self, cli, args=None, input=None, env=None, catch_exceptions=True, color=False, **extra):
        args = args or []
        exc_info = None
        with self.isolation(input=input, env=env, color=color) as (out, err):
            exit_code = 0
            try:
                cli.main(args=args, **extra)
            except SystemExit as e:
                if e.code != 0:
                    exit_code = e.code
                    if not isinstance(e.code, int):
                        sys.stderr.write(str(e.code))
                        sys.stderr.write('\n')
                        exit_code = 1
            except Exception as e:
                if not catch_exceptions:
                    raise
                exc_info = sys.exc_info()
                exit_code = 1
                sys.stderr.write(str(e))
                sys.stderr.write('\n')
            finally:
                sys.stdout.seek(0)
                sys.stderr.seek(0)
                stdout = out.getvalue()
                stderr = err.getvalue()
        return Result(
            runner=self,
            stdout_bytes=stdout,
            stderr_bytes=stderr,
            exit_code=exit_code,
            exception=exc_info[1] if exc_info else None,
            exc_info=exc_info
        )