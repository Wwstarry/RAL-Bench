"""
A tiny, pure-Python subset of Typer implemented on top of Click.

This package is intended to be API-compatible with the core parts of Typer
used by this repository's test suite.
"""

from .main import Typer
from .params import Option, Argument
from .utils import echo
from .exceptions import Exit

__all__ = [
    "Typer",
    "Option",
    "Argument",
    "echo",
    "Exit",
]

# testing submodule must exist and provide CliRunner
from . import testing  # noqa: E402,F401