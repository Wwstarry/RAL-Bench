"""
A small, pure-Python subset of the watchdog package API used by the tests.

This is not a full reimplementation of watchdog; it provides a polling-based
Observer and the basic event/handler types.
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