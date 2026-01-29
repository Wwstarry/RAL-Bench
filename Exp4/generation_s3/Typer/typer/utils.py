from __future__ import annotations

import sys
from typing import Any


def echo(
    message: Any = "",
    *,
    nl: bool = True,
    err: bool = False,
    file=None,
) -> None:
    """Write a message to stdout/stderr, similar to Typer/Click."""
    if file is None:
        file = sys.stderr if err else sys.stdout
    text = str(message)
    if nl:
        file.write(text + "\n")
    else:
        file.write(text)
    file.flush()