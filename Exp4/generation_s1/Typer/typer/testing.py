import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union


@dataclass
class Result:
    exit_code: int
    stdout: str
    stderr: str
    exception: Optional[BaseException] = None

    @property
    def output(self) -> str:
        return (self.stdout or "") + (self.stderr or "")


class CliRunner:
    def invoke(
        self,
        app: Any,
        args: Union[str, List[str], tuple, None] = None,
        input: Optional[str] = None,
        catch_exceptions: bool = True,
        env: Optional[Dict[str, str]] = None,
        prog_name: Optional[str] = None,
    ) -> Result:
        if args is None:
            arg_list: List[str] = []
        elif isinstance(args, str):
            arg_list = args.split()
        else:
            arg_list = list(args)

        stdout_io = io.StringIO()
        stderr_io = io.StringIO()

        old_stdin = sys.stdin
        stdin_io = io.StringIO(input if input is not None else "")
        sys.stdin = stdin_io

        try:
            with redirect_stdout(stdout_io), redirect_stderr(stderr_io):
                try:
                    if hasattr(app, "main") and callable(getattr(app, "main")):
                        # Ensure we get a return code instead of SystemExit.
                        code = app.main(arg_list, prog_name=prog_name, standalone_mode=False)
                        exit_code = int(code or 0)
                    else:
                        code = app(arg_list)
                        exit_code = int(code or 0)
                    return Result(
                        exit_code=exit_code,
                        stdout=stdout_io.getvalue(),
                        stderr=stderr_io.getvalue(),
                        exception=None,
                    )
                except BaseException as e:
                    if not catch_exceptions:
                        raise
                    # Preserve the original exception object for tests.
                    # Derive exit_code similar to Click/Typer behavior.
                    exit_code = 1
                    if isinstance(e, SystemExit):
                        try:
                            exit_code = int(e.code or 0)
                        except Exception:
                            exit_code = 1
                    return Result(
                        exit_code=exit_code,
                        stdout=stdout_io.getvalue(),
                        stderr=stderr_io.getvalue(),
                        exception=e,
                    )
        finally:
            sys.stdin = old_stdin