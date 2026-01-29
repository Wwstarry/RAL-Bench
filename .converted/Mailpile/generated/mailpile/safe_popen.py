# -*- coding: utf-8 -*-
"""
Safe subprocess wrapper and pipe helpers.

This module provides a very small, test-friendly subset of Mailpile's
safe_popen utilities:
- Popen: wrapper around subprocess.Popen that defaults to safe settings
- safe_popen: convenience function
- MakePopenUnsafe: compatibility stub (no-op here)
- PIPE helpers (inherit from subprocess)
"""



import os
import subprocess
from typing import Any, Dict, Optional, Sequence, Union

PIPE = subprocess.PIPE
STDOUT = subprocess.STDOUT
DEVNULL = subprocess.DEVNULL


def _sanitize_env(env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    base = dict(os.environ)
    if env:
        base.update({str(k): str(v) for k, v in list(env.items())})
    return base


class SafePopen(subprocess.Popen):
    """
    A safer default Popen:
    - shell=False unless explicitly requested
    - close_fds=True on POSIX
    - env sanitized/merged with os.environ
    """

    def __init__(
        self,
        args: Union[str, Sequence[str]],
        stdin: Any = None,
        stdout: Any = None,
        stderr: Any = None,
        shell: bool = False,
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        close_fds: Optional[bool] = None,
        **kwargs: Any,
    ):
        if close_fds is None:
            close_fds = (os.name != "nt")
        kwargs.setdefault("text", False)
        super().__init__(
            args,
            stdin=stdin,
            stdout=stdout,
            stderr=stderr,
            shell=shell,
            cwd=cwd,
            env=_sanitize_env(env),
            close_fds=close_fds,
            **kwargs,
        )


def Popen(*args: Any, **kwargs: Any) -> SafePopen:
    return SafePopen(*args, **kwargs)


def safe_popen(*args: Any, **kwargs: Any) -> SafePopen:
    return SafePopen(*args, **kwargs)


def MakePopenUnsafe() -> None:
    """
    Compatibility stub.

    The upstream Mailpile historically had logic to relax restrictions in
    controlled contexts. This benchmark slice doesn't enforce extra
    restrictions beyond safe defaults, so this is a no-op.
    """
    return None