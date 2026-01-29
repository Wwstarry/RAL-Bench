import sys
import io
import contextlib
import os
import shlex
from .core import Context, Command, Group, Exit, UsageError

class Result:
    def __init__(self, exit_code, output, exception):
        self.exit_code = exit_code
        self.output = output
        self.exception = exception

    @property
    def stdout(self):
        return self.output

    @property
    def stderr(self):
        # For simplicity, stderr is merged into output in this implementation
        return ""

class CliRunner:
    def __init__(self, env=None, mix_stderr=False):
        self.env = env or {}
        self.mix_stderr = mix_stderr

    @contextlib.contextmanager
    def isolated_filesystem(self):
        import tempfile
        import shutil

        cwd = os.getcwd()
        tempdir = tempfile.mkdtemp()
        try:
            os.chdir(tempdir)
            yield
        finally:
            os.chdir(cwd)
            shutil.rmtree(tempdir)

    def invoke(self, cli, args=None, input=None, env=None, catch_exceptions=True):
        args = args or []
        if isinstance(args, str):
            args = shlex.split(args)
        env = env or {}
        env = {**os.environ, **self.env, **env}

        # Setup input
        if input is not None:
            stdin = io.StringIO(input)
        else:
            stdin = io.StringIO()

        # Capture output
        stdout = io.StringIO()
        stderr = io.StringIO()

        # Patch sys.stdin, stdout, stderr
        orig_stdin = sys.stdin
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr

        sys.stdin = stdin
        sys.stdout = stdout
        sys.stderr = stderr if not self.mix_stderr else stdout

        # Patch os.environ
        orig_environ = os.environ
        os.environ = env

        exception = None
        exit_code = 0
        try:
            ctx = Context(cli)
            ctx.stdout = stdout
            ctx.stderr = stderr
            exit_code = cli.invoke(ctx, args)
        except Exit as e:
            exit_code = e.exit_code
        except Exception as e:
            if catch_exceptions:
                exception = e
                exit_code = 1
            else:
                raise
        finally:
            sys.stdin = orig_stdin
            sys.stdout = orig_stdout
            sys.stderr = orig_stderr
            os.environ = orig_environ

        output = stdout.getvalue()
        if not self.mix_stderr:
            output += stderr.getvalue()

        return Result(exit_code, output, exception)