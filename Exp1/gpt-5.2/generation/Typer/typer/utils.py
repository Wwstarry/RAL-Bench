from __future__ import annotations

import sys
from typing import Any


def echo(message: Any = "", nl: bool = True, err: bool = False) -> None:
    text = "" if message is None else str(message)
    if nl:
        text += "\n"
    stream = sys.stderr if err else sys.stdout
    stream.write(text)
    stream.flush()