"""
Typer - A minimal CLI framework compatible with Typer's core API.
"""

from .core import Typer, Option, Argument, echo, Exit
from . import testing

__all__ = [
    "Typer",
    "Option", 
    "Argument",
    "echo",
    "Exit",
    "testing",
]

__version__ = "0.1.0"