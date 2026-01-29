import sys
import io
import shlex
from contextlib import contextmanager
from .core import BaseCommand

class Result:
    def __init__(self, runner, exit_code, exception, exc_info=None, return_value=None):
        self.runner = runner
        self.exit_code = exit_code
        self.exception = exception
        self.exc_info = exc_info
        self.return_value = return_value
        self.stdout_bytes = runner.get_default_prog_name(runner).encode('utf-8') # Placeholder
        self._stdout = runner._stdout.getvalue()
        self._stderr = runner._stderr.getvalue()

    @property
    def output(self):
        return self._stdout

    @property
    def stdout(self):
        return self._stdout

    @property
    def stderr(self):
        return self._stderr

    def __repr__(self):
        return f'<Result {self.exception and "exception" or "ok"}>'

class CliRunner:
    def __init__(self, charset='utf-8', env=None, echo_stdin=False, mix_stderr=True):
        self.charset = charset
        self.env = env or {}
        self.echo_stdin = echo_stdin
        self.mix_stderr = mix_stderr
        self._stdout = io.StringIO()
        self._stderr = io.StringIO()

    def get_default_prog_name(self, cli):
        return 'cli'

    @contextmanager
    def isolation(self, input=None, env=None, color=False):
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        sys.stdout = self._stdout
        sys.stderr = self._stderr if not self.mix_stderr else self._stdout
        
        # Mock stdin if input provided
        old_stdin = sys.stdin
        if input is not None:
            if isinstance(input, str):
                input = input.encode(self.charset)
            sys.stdin = io.TextIOWrapper(io.BytesIO(input), encoding=self.charset)
            
        try:
            yield
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
            sys.stdin = old_stdin

    def invoke(self, cli, args=None, input=None, env=None, catch_exceptions=True, color=False, **extra):
        if isinstance(args, str):
            args = shlex.split(args)
        
        exc_info = None
        exception = None
        exit_code = 0
        return_value = None

        with self.isolation(input=input, env=env, color=color):
            try:
                if isinstance(cli, BaseCommand):
                    return_value = cli.main(args=args or [], standalone_mode=False, **extra)
                    if return_value is None:
                        exit_code = 0
                    elif isinstance(return_value, int):
                        exit_code = return_value
                else:
                    # Support for invoking functions directly if they aren't commands (rare in click tests but possible)
                    cli(args or [])
            except SystemExit as e:
                exit_code = e.code if e.code is not None else 0
            except Exception as e:
                if not catch_exceptions:
                    raise
                exception = e
                exc_info = sys.exc_info()
                exit_code = 1
                
                # In real click, this prints the exception to stderr if not standalone
                # For testing, we capture it
                import traceback
                traceback.print_exception(*exc_info, file=sys.stderr)

        return Result(self, exit_code, exception, exc_info, return_value)