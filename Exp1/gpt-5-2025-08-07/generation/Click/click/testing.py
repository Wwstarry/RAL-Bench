import os
import sys
import io
import shlex
import contextlib
from dataclasses import dataclass


@dataclass
class Result:
    runner: "CliRunner"
    stdout: str
    stderr: str
    exit_code: int
    exception: BaseException = None
    exc_info: tuple | None = None

    @property
    def output(self):
        # By default, Click returns stdout as output (unless mix_stderr=True)
        return self.stdout


class CliRunner:
    def __init__(self, env=None, echo_stdin=False, mix_stderr=False):
        self.env = env or {}
        self.echo_stdin = echo_stdin
        self.default_mix_stderr = mix_stderr

    def isolate_env(self, extra_env):
        env = os.environ.copy()
        env.update(extra_env or {})
        return env

    def invoke(
        self,
        cli,
        args=None,
        input=None,
        env=None,
        catch_exceptions=True,
        color=False,
        mix_stderr=None,
    ):
        if mix_stderr is None:
            mix_stderr = self.default_mix_stderr

        if args is None:
            args_list = []
        elif isinstance(args, str):
            args_list = shlex.split(args)
        elif isinstance(args, (list, tuple)):
            args_list = list(args)
        else:
            raise TypeError("args must be None, str, list or tuple")

        # Prepare IO capture
        stdout = io.StringIO()
        stderr = io.StringIO()
        # Prepare stdin
        if input is None:
            stdin = io.StringIO("")
        elif isinstance(input, (str, bytes)):
            if isinstance(input, bytes):
                input = input.decode()
            stdin = io.StringIO(input)
        else:
            # file-like
            stdin = input

        environ = os.environ.copy()
        if self.env:
            environ.update(self.env)
        if env:
            environ.update(env)

        exit_code = 0
        exc = None
        exc_info = None

        # Swap stdio and environment
        with contextlib.ExitStack() as stack:
            stack.enter_context(_patched_environ(environ))
            stack.enter_context(contextlib.redirect_stdout(stdout))
            stack.enter_context(contextlib.redirect_stderr(stderr))
            old_stdin = sys.stdin
            sys.stdin = stdin
            try:
                # In click, runner passes standalone_mode=False
                cli.main(args=args_list, prog_name=getattr(cli, "name", None), standalone_mode=False, obj=None)
            except SystemExit as e:
                # SystemExit may be raised for help exit
                exit_code = int(e.code) if e.code is not None else 0
            except BaseException as e:
                exc = e
                exc_info = sys.exc_info()
                if catch_exceptions:
                    exit_code = getattr(e, "exit_code", 1)
                else:
                    # re-raise to keep original traceback in tests when required
                    raise
            finally:
                sys.stdin = old_stdin

        out = stdout.getvalue()
        err = stderr.getvalue()
        if mix_stderr:
            out = out + err
            err = ""

        return Result(self, stdout=out, stderr=err, exit_code=exit_code, exception=exc, exc_info=exc_info)


@contextlib.contextmanager
def _patched_environ(new_env):
    old_env = os.environ.copy()
    try:
        os.environ.clear()
        os.environ.update(new_env)
        yield
    finally:
        os.environ.clear()
        os.environ.update(old_env)