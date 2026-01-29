"""
A tiny, pure-Python subset of Typer's public API, sufficient for the tests in this kata.

This is NOT the real Typer project.
"""

from .main import Typer
from .params import Option, Argument, OptionInfo, ArgumentInfo
from .utils import echo
from .exceptions import Exit

# Expose testing as a submodule like real Typer
from . import testing  # noqa: F401

__all__ = [
    "Typer",
    "Option",
    "Argument",
    "OptionInfo",
    "ArgumentInfo",
    "echo",
    "Exit",
    "testing",
]