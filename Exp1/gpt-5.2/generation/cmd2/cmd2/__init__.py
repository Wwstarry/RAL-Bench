"""
Lightweight, pure-Python subset of the cmd2 project.

This repository provides a minimal API-compatible surface for common cmd2 use
cases (interactive command loop, parsing helpers, transcript testing, etc.).
"""

from .cmd2 import Cmd2, CommandResult, StdSim, with_default_category

__all__ = [
    "Cmd2",
    "CommandResult",
    "StdSim",
    "with_default_category",
]