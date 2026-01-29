"""
Various helper utilities that appear in the public API surface of the
original project.  Only a thin subset is implemented here.
"""
from __future__ import annotations

import contextlib
import io
import sys
from typing import Iterator, Tuple


@contextlib.contextmanager
def capture_output(app) -> Iterator[Tuple[io.StringIO, io.StringIO]]:
    """
    Context manager that redirects an *app*'s ``stdout`` and ``stderr``
    to in-memory buffers while the body of the `with` statement is
    executed.

    Examples
    --------
    >>> with app.capture_output() as (out, err):
    ...     app.onecmd("help")
    >>> text = out.getvalue()
    """
    new_out = io.StringIO()
    new_err = io.StringIO()

    # The application always prints to ``app.stdout`` or, for errors,
    # ``app.stderr``.  We leave the global ``sys.stdout`` untouched
    # because that is how the real cmd2 behaves.
    old_out = getattr(app, "stdout", sys.stdout)
    old_err = getattr(app, "stderr", sys.stderr)

    app.stdout = new_out
    app.stderr = new_err
    try:
        yield (new_out, new_err)
    finally:
        app.stdout = old_out
        app.stderr = old_err