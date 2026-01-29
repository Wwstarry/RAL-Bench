from __future__ import annotations

import contextlib
import io
import re
import sys
from typing import Iterator, Tuple


_ANSI_RE = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")


def strip_ansi(text: str) -> str:
    if text is None:
        return ""
    return _ANSI_RE.sub("", text)


def ensure_str(s) -> str:
    if s is None:
        return ""
    if isinstance(s, bytes):
        return s.decode(errors="replace")
    return str(s)


@contextlib.contextmanager
def redirect_std(target_stdout, target_stderr=None) -> Iterator[None]:
    """Redirect sys.stdout and sys.stderr within context."""
    if target_stderr is None:
        target_stderr = target_stdout
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = target_stdout, target_stderr
    try:
        yield
    finally:
        sys.stdout, sys.stderr = old_out, old_err


@contextlib.contextmanager
def capture_std() -> Iterator[Tuple[io.StringIO, io.StringIO]]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_std(out, err):
        yield out, err


@contextlib.contextmanager
def capture_output() -> Iterator[Tuple[io.StringIO, io.StringIO]]:
    # alias for capture_std
    with capture_std() as pair:
        yield pair