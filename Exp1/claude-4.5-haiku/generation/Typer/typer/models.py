"""Models for Typer options and arguments."""

from typing import Any, Optional


class Option:
    """Represents a command-line option."""

    def __init__(
        self,
        default: Any = None,
        *,
        help: Optional[str] = None,
        short_name: Optional[str] = None,
    ):
        self.default = default
        self.help = help
        self.short_name = short_name


class Argument:
    """Represents a command-line argument."""

    def __init__(
        self,
        default: Any = None,
        *,
        help: Optional[str] = None,
    ):
        self.default = default
        self.help = help