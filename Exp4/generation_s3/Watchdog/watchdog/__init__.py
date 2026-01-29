"""
A tiny, pure-Python subset of the `watchdog` package API.

This implementation is intended for educational/testing use and provides
polling-based filesystem monitoring compatible with the core parts of the
reference watchdog project used by the test suite.
"""

from .events import FileSystemEventHandler
from .observers import Observer

__all__ = ["Observer", "FileSystemEventHandler"]

# Optional metadata (some code may introspect these)
__version__ = "0.0.0"