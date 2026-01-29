"""
Pure-Python minimal subset of the watchdog package.

This implementation is intended to be API-compatible with the core parts used by
tests that expect the reference watchdog project's basic interfaces.
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
from .observers import Observer

__all__ = [
    "Observer",
    "FileSystemEventHandler",
    "FileSystemEvent",
    "FileCreatedEvent",
    "FileModifiedEvent",
    "FileDeletedEvent",
    "DirCreatedEvent",
    "DirModifiedEvent",
    "DirDeletedEvent",
]

__version__ = "0.0.0"