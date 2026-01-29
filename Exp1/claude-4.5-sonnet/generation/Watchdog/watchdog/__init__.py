"""
Pure Python filesystem monitoring library.
API-compatible with core parts of watchdog.
"""

__version__ = "1.0.0"

from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEvent,
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    DirCreatedEvent,
    DirModifiedEvent,
    DirDeletedEvent,
)

__all__ = [
    "Observer",
    "FileSystemEvent",
    "FileSystemEventHandler",
    "FileCreatedEvent",
    "FileModifiedEvent",
    "FileDeletedEvent",
    "DirCreatedEvent",
    "DirModifiedEvent",
    "DirDeletedEvent",
]