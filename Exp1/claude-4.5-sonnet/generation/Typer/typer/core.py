"""Core utilities for Typer."""

import sys
from typing import Any, Optional


class Exit(Exception):
    """Exception to exit with a specific code."""
    
    def __init__(self, code: int = 0):
        self.code = code
        super().__init__()


def echo(message: Any = "", file: Optional[Any] = None, nl: bool = True, err: bool = False) -> None:
    """Print a message to the console."""
    if file is None:
        file = sys.stderr if err else sys.stdout
    
    if nl:
        print(message, file=file)
    else:
        print(message, end="", file=file)