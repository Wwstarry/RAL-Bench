from __future__ import annotations

import contextlib
import io
import os
import shlex
import traceback
from dataclasses import dataclass
from typing import Any, Callable

from .exceptions import Exit


@dataclass
class Result:
    exit_code: int
    stdout: str
    stderr: str
    output: str
    exception: Exception | None = None


class CliRunner:
    def __init__(self, *, mix_stderr: bool = False):
        self.mix_stderr = mix_stderr

    def invoke(
        self,
        app: Any,
        args: str | list[str] | None = None,
        input: str | None = None,
        env: dict | None = None,
        catch_exceptions: bool = True,
        prog_name: str | None = None,
    ) -> Result:
        if args is None:
            argv = []
        elif isinstance(args, str):
            argv = shlex.split(args)
        else:
            argv = list(args)

        stdin = io.StringIO(input if input is not None else "")
        stdout = io.StringIO()
        stderr = stdout if self.mix_stderr else io.StringIO()

        old_env = os.environ.copy()
        if env:
            os.environ.update({str(k): str(v) for k, v in env.items()})

        exit_code = 0
        exc: Exception | None = None

        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr), contextlib.redirect_stdin(stdin):
                try:
                    if hasattr(app, "__call__"):
                        # Our Typer app returns an int exit code
                        rc = app(args=argv, prog_name=prog_name)
                        if isinstance(rc, int):
                            exit_code = rc
                        else:
                            exit_code = 0
                    elif isinstance(app, Callable):
                        res = app(*argv)
                        exit_code = int(res) if isinstance(res, int) else 0
                    else:
                        raise TypeError("App is not callable")
                except Exit as e:
                    exit_code = int(getattr(e, "exit_code", getattr(e, "code", 0)))
                except SystemExit as e:
                    code = e.code
                    exit_code = int(code) if isinstance(code, int) else (0 if code is None else 1)
                except Exception as e:  # noqa: BLE001
                    if not catch_exceptions:
                        raise
                    exc = e
                    exit_code = 1
                    # Keep output minimal; include traceback for debugging if tests expect it.
                    tb = traceback.format_exc()
                    if tb:
                        (stderr if not self.mix_stderr else stdout).write(tb)
        finally:
            os.environ.clear()
            os.environ.update(old_env)

        out_s = stdout.getvalue()
        err_s = "" if self.mix_stderr else stderr.getvalue()
        output = out_s if not self.mix_stderr else out_s
        if not self.mix_stderr:
            output = out_s  # Match common expectation: output==stdout when not mixing

        return Result(exit_code=exit_code, stdout=out_s, stderr=err_s, output=output, exception=exc)