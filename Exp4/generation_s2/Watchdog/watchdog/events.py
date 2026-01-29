from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class FileSystemEvent:
    src_path: str
    event_type: str
    is_directory: bool = False

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(src_path={self.src_path!r}, "
            f"event_type={self.event_type!r}, is_directory={self.is_directory!r})"
        )


class FileSystemCreatedEvent(FileSystemEvent):
    def __init__(self, src_path: str, is_directory: bool = False):
        super().__init__(src_path=os.fspath(src_path), event_type="created", is_directory=is_directory)


class FileSystemModifiedEvent(FileSystemEvent):
    def __init__(self, src_path: str, is_directory: bool = False):
        super().__init__(src_path=os.fspath(src_path), event_type="modified", is_directory=is_directory)


class FileSystemDeletedEvent(FileSystemEvent):
    def __init__(self, src_path: str, is_directory: bool = False):
        super().__init__(src_path=os.fspath(src_path), event_type="deleted", is_directory=is_directory)


class FileCreatedEvent(FileSystemCreatedEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path, is_directory=False)


class FileModifiedEvent(FileSystemModifiedEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path, is_directory=False)


class FileDeletedEvent(FileSystemDeletedEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path, is_directory=False)


class DirCreatedEvent(FileSystemCreatedEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path, is_directory=True)


class DirModifiedEvent(FileSystemModifiedEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path, is_directory=True)


class DirDeletedEvent(FileSystemDeletedEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path, is_directory=True)


class FileSystemEventHandler:
    """
    Matches the watchdog API shape used by tests.

    Users override on_created/on_modified/on_deleted (and optionally others).
    """

    def dispatch(self, event: FileSystemEvent) -> None:
        et = getattr(event, "event_type", None)
        if et == "created":
            self.on_created(event)
        elif et == "modified":
            self.on_modified(event)
        elif et == "deleted":
            self.on_deleted(event)
        else:
            self.on_any_event(event)

    def on_any_event(self, event: FileSystemEvent) -> None:
        pass

    def on_created(self, event: FileSystemEvent) -> None:
        pass

    def on_modified(self, event: FileSystemEvent) -> None:
        pass

    def on_deleted(self, event: FileSystemEvent) -> None:
        pass