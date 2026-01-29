import os


class FileSystemEvent:
    """
    Basic file system event with source path and event type.

    Attributes:
        src_path (str): Path of the file or directory that triggered the event.
        is_directory (bool): True if the event refers to a directory.
        event_type (str): One of 'created', 'modified', 'deleted'.
    """

    def __init__(self, src_path, is_directory=False, event_type=None):
        self.src_path = src_path
        self.is_directory = bool(is_directory)
        self.event_type = event_type

    def __repr__(self):
        kind = "Dir" if self.is_directory else "File"
        return f"<{kind}{self.__class__.__name__}(event_type={self.event_type!r}, src_path={self.src_path!r})>"


# File event classes
class FileCreatedEvent(FileSystemEvent):
    def __init__(self, src_path):
        super().__init__(src_path, is_directory=False, event_type="created")


class FileModifiedEvent(FileSystemEvent):
    def __init__(self, src_path):
        super().__init__(src_path, is_directory=False, event_type="modified")


class FileDeletedEvent(FileSystemEvent):
    def __init__(self, src_path):
        super().__init__(src_path, is_directory=False, event_type="deleted")


# Directory event classes (not used by the polling observer, but kept for compatibility)
class DirCreatedEvent(FileSystemEvent):
    def __init__(self, src_path):
        super().__init__(src_path, is_directory=True, event_type="created")


class DirModifiedEvent(FileSystemEvent):
    def __init__(self, src_path):
        super().__init__(src_path, is_directory=True, event_type="modified")


class DirDeletedEvent(FileSystemEvent):
    def __init__(self, src_path):
        super().__init__(src_path, is_directory=True, event_type="deleted")


class FileSystemEventHandler:
    """
    Base file system event handler with overridable callbacks.

    Subclasses can override the on_created, on_modified, on_deleted methods to
    receive notifications. Alternatively, override on_any_event to intercept
    all events.
    """

    def dispatch(self, event):
        """
        Dispatches events to the appropriate methods.

        Calls on_any_event first, then the event specific callback if available.
        """
        try:
            self.on_any_event(event)
        except Exception:
            # Handlers should not raise to break observer dispatch
            pass

        if event.event_type == "created":
            self.on_created(event)
        elif event.event_type == "modified":
            self.on_modified(event)
        elif event.event_type == "deleted":
            self.on_deleted(event)

    def on_any_event(self, event):
        """Called for any event. Default does nothing."""
        pass

    def on_created(self, event):
        """Called when a file or directory is created."""
        pass

    def on_modified(self, event):
        """Called when a file or directory is modified."""
        pass

    def on_deleted(self, event):
        """Called when a file or directory is deleted."""
        pass


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