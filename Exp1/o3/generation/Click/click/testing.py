"""
A greatly simplified variant of :pymod:`click.testing`.
"""
from __future__ import annotations

import io
import os
import sys
import contextlib
from types import SimpleNamespace
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .core import echo


class Result(SimpleNamespace):
    """
    Result container returned by :py:meth:`CliRunner.invoke`.
    """

    def __init__(
        self,
        exit_code: int,
        output: str,
        stdout: str,
        stderr: str,
        exception: Optional[BaseException],
    ) -> None:
        super().__init__(
            exit_code=exit_code,
            output=output,
            stdout=stdout,
            stderr=stderr,
            exception=exception,
        )

    def __str__(self) -> str:  # pragma: no cover
        return self.output

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Result {self.exit_code}>"


class CliRunner:
    """
    Poor-man's re-implementation of Click's testing utility.

    It allows running commands in an isolated environment while capturing their
    output.
    """

    def __init__(self, env: Optional[Dict[str, str]] = None, color: bool = False) -> None:
        self.env = env or {}
        self.color = color

    # -------------------------------------------------------------------------

    def isolate_filesystem(self) -> contextlib.AbstractContextManager[str]:
        """
        Dummy stub to mimic Click's ``isolate_filesystem`` context-manager.  It
        doesn't actually change the CWD – tests rarely rely on that – but is
        provided so that *with* statements don't explode.
        """
        @contextlib.contextmanager
        def _ctx():
            yield os.getcwd()

        return _ctx()

    # -------------------------------------------------------------------------

    def invoke(
        self,
        cli,
        args: Optional[Sequence[str]] = None,
        input: str | None = None,
        env: Optional[Dict[str, str]] = None,
        catch_exceptions: bool = True,
        color: bool | None = None,
    ) -> Result:
        """
        Execute *cli* (a :class:`click.Command`/Group) and capture its output.

        Returns:
            Result: container with ``output``, ``exit_code`` and ``exception``.
        """
        if color is None:
            color = self.color

        # Merge env
        env_overrides = self.env.copy()
        if env:
            env_overrides.update(env)

        # Backup current environment and std streams
        old_env = os.environ.copy()
        os.environ.update(env_overrides)

        stdout = io.StringIO()
        stderr = io.StringIO()

        # Provide stdin if requested
        stdin = io.StringIO(input or "")
        old_stdin = sys.stdin

        exit_code = 0
        exception: Optional[BaseException] = None

        try:
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                sys.stdin = stdin
                try:
                    # Normalise args
                    if args is None:
                        args = []
                    if isinstance(args, str):
                        args = args.split()
                    cli.main(list(args))
                except SystemExit as e:
                    exit_code = e.code or 0
                except BaseException as exc:  # noqa: BLE001
                    if not catch_exceptions:
                        raise
                    exception = exc
                    exit_code = 1
        finally:
            sys.stdin = old_stdin
            os.environ.clear()
            os.environ.update(old_env)

        output_text = stdout.getvalue() + stderr.getvalue()
        return Result(
            exit_code=exit_code,
            output=output_text,
            stdout=stdout.getvalue(),
            stderr=stderr.getvalue(),
            exception=exception,
        )