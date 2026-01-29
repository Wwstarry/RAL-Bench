"""Lightweight, pure-Python subset of the cmd2 project.

This package provides a minimal API surface compatible with core parts of cmd2
used by transcript-based testing and simple interactive applications.
"""

from .cmd2 import Cmd2

__all__ = ["Cmd2"]