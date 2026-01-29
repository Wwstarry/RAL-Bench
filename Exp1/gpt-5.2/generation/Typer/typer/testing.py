from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional, Sequence, Union


@dataclass
class Result:
    stdout: str
    stderr: str
    exit_code: int
    exception: Optional[BaseException] = None

    @property
    def output(self) -> str:
        return (self.stdout or "") + (self.stderr or "")


class CliRunner:
    def __init__(self, mix_stderr: bool = False) -> None:
        self.mix_stderr = mix_stderr

    def invoke(
        self,
        app: Any,
        args: Union[str, Sequence[str], None] = None,
        prog_name: Optional[str] = None,
        catch_exceptions: bool = True,
    ) -> Result:
        if args is None:
            argv = []
        elif isinstance(args, str):
            # simple split; sufficient for tests
            argv = [a for a in args.split(" ") if a != ""]
        else:
            argv = list(args)

        # If it's our Typer, call its internal dispatch for capture.
        if hasattr(app, "_dispatch"):
            try:
                return app._dispatch(argv, prog=prog_name or getattr(app, "name", None) or "app")
            except Exception as e:
                if not catch_exceptions:
                    raise
                return Result("", f"{e}\n", 1, e)

        # Otherwise try calling it like a function and capture SystemExit.
        try:
            app(args=argv, prog_name=prog_name)
        except SystemExit as e:
            code = int(e.code) if e.code is not None else 0
            return Result("", "", code, e)
        except BaseException as e:
            if not catch_exceptions:
                raise
            return Result("", f"{e}\n", 1, e)

        return Result("", "", 0, None)