"""Exceptions used by this lightweight cmd2-compatible implementation.

The real cmd2 project supports older Python versions. Our test environment may
also run on versions where PEP 604 (X | Y union types) isn't supported. Keep
type annotations compatible by using typing.Optional instead of the | operator.
"""

from __future__ import annotations

from typing import Optional


class CommandError(Exception):
    """Base error for command-related failures."""


class Cmd2ArgparseError(CommandError):
    """Raised when argparse would normally call SystemExit."""

    def __init__(self, message: str = "", *, usage: Optional[str] = None, status: int = 2):
        super().__init__(message)
        self.message = message
        self.usage = usage
        self.status = status