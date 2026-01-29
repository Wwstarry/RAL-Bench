"""Utility functions for Typer."""

import sys
from typing import Optional


def echo(message: str = "", **kwargs: dict) -> None:
    """Print a message to the console."""
    print(message, **kwargs)


class Exit(Exception):
    """Exception to exit with a specific status code."""

    def __init__(self, exit_code: int = 0):
        self.exit_code = exit_code
        super().__init__(f"Exit with code {exit_code}")