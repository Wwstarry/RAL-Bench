"""
Minimal stub of the ``watchdog`` top-level package required by the tests.
Only the subset of functionality exercised by the black-box tests is
implemented.  For full-featured file-system monitoring please use the real
*watchdog* PyPI package.

This simplified implementation provides:

* Event classes (see ``watchdog.events``)
* A basic polling observer (see ``watchdog.observers``)
"""
# Re-export the public API expected by tests
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
    # events
    "FileSystemEvent",
    "FileCreatedEvent",
    "FileModifiedEvent",
    "FileDeletedEvent",
    "DirCreatedEvent",
    "DirModifiedEvent",
    "DirDeletedEvent",
    "FileSystemEventHandler",
    # observers
    "Observer",
]