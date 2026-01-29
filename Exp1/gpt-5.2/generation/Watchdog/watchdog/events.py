from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FileSystemEvent:
    src_path: str
    is_directory: bool = False
    event_type: str = "unknown"


class FileSystemMovedEvent(FileSystemEvent):
    # Not required by current tests; defined for compatibility.
    def __init__(self, src_path: str, dest_path: str, is_directory: bool = False):
        object.__setattr__(self, "src_path", src_path)
        object.__setattr__(self, "is_directory", is_directory)
        object.__setattr__(self, "event_type", "moved")
        self.dest_path = dest_path


class FileCreatedEvent(FileSystemEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path=os.fspath(src_path), is_directory=False, event_type="created")


class FileModifiedEvent(FileSystemEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path=os.fspath(src_path), is_directory=False, event_type="modified")


class FileDeletedEvent(FileSystemEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path=os.fspath(src_path), is_directory=False, event_type="deleted")


class DirCreatedEvent(FileSystemEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path=os.fspath(src_path), is_directory=True, event_type="created")


class DirModifiedEvent(FileSystemEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path=os.fspath(src_path), is_directory=True, event_type="modified")


class DirDeletedEvent(FileSystemEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path=os.fspath(src_path), is_directory=True, event_type="deleted")


class FileSystemEventHandler:
    """
    Minimal compatible API with watchdog.events.FileSystemEventHandler.

    Tests typically subclass this and override on_created/on_modified/on_deleted.
    """

    def dispatch(self, event: FileSystemEvent) -> None:
        self.on_any_event(event)
        if event.event_type == "created":
            self.on_created(event)
        elif event.event_type == "modified":
            self.on_modified(event)
        elif event.event_type == "deleted":
            self.on_deleted(event)
        elif event.event_type == "moved":
            self.on_moved(event)

    def on_any_event(self, event: FileSystemEvent) -> None:
        pass

    def on_created(self, event: FileSystemEvent) -> None:
        pass

    def on_modified(self, event: FileSystemEvent) -> None:
        pass

    def on_deleted(self, event: FileSystemEvent) -> None:
        pass

    def on_moved(self, event: FileSystemEvent) -> None:
        pass