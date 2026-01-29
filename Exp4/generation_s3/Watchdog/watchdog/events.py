from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FileSystemEvent:
    event_type: str
    src_path: str
    is_directory: bool = False


class FileCreatedEvent(FileSystemEvent):
    def __init__(self, path: str, is_directory: bool = False):
        super().__init__(event_type="created", src_path=path, is_directory=is_directory)


class FileModifiedEvent(FileSystemEvent):
    def __init__(self, path: str, is_directory: bool = False):
        super().__init__(event_type="modified", src_path=path, is_directory=is_directory)


class FileDeletedEvent(FileSystemEvent):
    def __init__(self, path: str, is_directory: bool = False):
        super().__init__(event_type="deleted", src_path=path, is_directory=is_directory)


class FileMovedEvent(FileSystemEvent):
    # Optional; provided for compatibility even if not used by tests.
    def __init__(self, src_path: str, dest_path: str, is_directory: bool = False):
        # Keep attributes similar to watchdog: src_path + dest_path.
        object.__setattr__(self, "dest_path", dest_path)  # type: ignore[attr-defined]
        super().__init__(event_type="moved", src_path=src_path, is_directory=is_directory)


class FileSystemEventHandler:
    """
    Base event handler with overridable callbacks.
    """

    def dispatch(self, event: FileSystemEvent) -> None:
        self.on_any_event(event)
        et = getattr(event, "event_type", None)
        if et == "created":
            self.on_created(event)
        elif et == "modified":
            self.on_modified(event)
        elif et == "deleted":
            self.on_deleted(event)
        elif et == "moved":
            self.on_moved(event)

    def on_any_event(self, event: FileSystemEvent) -> None:
        return None

    def on_created(self, event: FileSystemEvent) -> None:
        return None

    def on_modified(self, event: FileSystemEvent) -> None:
        return None

    def on_deleted(self, event: FileSystemEvent) -> None:
        return None

    def on_moved(self, event: FileSystemEvent) -> None:
        return None