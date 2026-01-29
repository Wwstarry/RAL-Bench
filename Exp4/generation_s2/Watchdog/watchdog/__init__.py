"""
A tiny, pure-Python subset of the `watchdog` project.

This package is intended to be API-compatible with the core pieces used by the
tests in ./tests/Watchdog/.

Only a polling-based observer is provided.
"""

from .events import (
    FileSystemEvent,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    DirCreatedEvent,
    DirModifiedEvent,
    DirDeletedEvent,
    FileSystemEventHandler,
)

__all__ = [
    "FileSystemEvent",
    "FileCreatedEvent",
    "FileModifiedEvent",
    "FileDeletedEvent",
    "DirCreatedEvent",
    "DirModifiedEvent",
    "DirDeletedEvent",
    "FileSystemEventHandler",
]