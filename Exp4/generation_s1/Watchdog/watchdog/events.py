from __future__ import annotations


class FileSystemEvent:
    """
    Minimal event model compatible with the subset commonly used in watchdog.

    Attributes:
      - src_path: str
      - event_type: "created" | "modified" | "deleted"
      - is_directory: bool
    """

    def __init__(self, src_path: str, event_type: str, is_directory: bool = False):
        self.src_path = src_path
        self.event_type = event_type
        self.is_directory = bool(is_directory)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} src_path={self.src_path!r} event_type={self.event_type!r} is_directory={self.is_directory!r}>"


class FileCreatedEvent(FileSystemEvent):
    def __init__(self, src_path: str, is_directory: bool = False):
        super().__init__(src_path=src_path, event_type="created", is_directory=is_directory)


class FileModifiedEvent(FileSystemEvent):
    def __init__(self, src_path: str, is_directory: bool = False):
        super().__init__(src_path=src_path, event_type="modified", is_directory=is_directory)


class FileDeletedEvent(FileSystemEvent):
    def __init__(self, src_path: str, is_directory: bool = False):
        super().__init__(src_path=src_path, event_type="deleted", is_directory=is_directory)


# Optional directory events (some tests might reference these names)
class DirCreatedEvent(FileCreatedEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path=src_path, is_directory=True)


class DirModifiedEvent(FileModifiedEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path=src_path, is_directory=True)


class DirDeletedEvent(FileDeletedEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path=src_path, is_directory=True)


class FileSystemEventHandler:
    """
    Minimal handler API. Users can override callbacks.

    dispatch(event) calls:
      - on_any_event(event)
      - on_created/on_modified/on_deleted depending on event.event_type
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

    def on_any_event(self, event: FileSystemEvent) -> None:
        pass

    def on_created(self, event: FileSystemEvent) -> None:
        pass

    def on_modified(self, event: FileSystemEvent) -> None:
        pass

    def on_deleted(self, event: FileSystemEvent) -> None:
        pass