import os

# Event types
EVENT_TYPE_MOVED = 'moved'
EVENT_TYPE_DELETED = 'deleted'
EVENT_TYPE_CREATED = 'created'
EVENT_TYPE_MODIFIED = 'modified'


class FileSystemEvent:
    """Base file system event."""

    event_type = None
    """Event type string."""

    def __init__(self, src_path):
        self._src_path = src_path

    @property
    def src_path(self):
        """Source path for the event."""
        return self._src_path

    @property
    def is_directory(self):
        """True if event was emitted for a directory; False otherwise."""
        return os.path.isdir(self.src_path)

    def __repr__(self):
        return (f"<{type(self).__name__}: event_type={self.event_type}, "
                f"src_path='{self.src_path}', is_directory={self.is_directory}>")


# Created Events
class FileCreatedEvent(FileSystemEvent):
    """File system event representing file creation."""
    event_type = EVENT_TYPE_CREATED


class DirCreatedEvent(FileCreatedEvent):
    """File system event representing directory creation."""
    @property
    def is_directory(self):
        return True


# Deleted Events
class FileDeletedEvent(FileSystemEvent):
    """File system event representing file deletion."""
    event_type = EVENT_TYPE_DELETED

    def __init__(self, src_path):
        self._src_path = src_path
        self._is_directory = False

    @property
    def is_directory(self):
        return self._is_directory


class DirDeletedEvent(FileDeletedEvent):
    """File system event representing directory deletion."""
    def __init__(self, src_path):
        self._src_path = src_path
        self._is_directory = True


# Modified Events
class FileModifiedEvent(FileSystemEvent):
    """File system event representing file modification."""
    event_type = EVENT_TYPE_MODIFIED


class DirModifiedEvent(FileModifiedEvent):
    """File system event representing directory modification."""
    @property
    def is_directory(self):
        return True


# Moved Events
class FileSystemMovedEvent(FileSystemEvent):
    """File system event representing a file or directory move."""
    event_type = EVENT_TYPE_MOVED

    def __init__(self, src_path, dest_path):
        super().__init__(src_path)
        self._dest_path = dest_path

    @property
    def dest_path(self):
        """The destination path of the move."""
        return self._dest_path

    @property
    def is_directory(self):
        return os.path.isdir(self.dest_path)


class FileMovedEvent(FileSystemMovedEvent):
    """File system event representing a file move."""


class DirMovedEvent(FileSystemMovedEvent):
    """File system event representing a directory move."""
    @property
    def is_directory(self):
        return True


class FileSystemEventHandler:
    """Base event handler that does nothing."""

    def dispatch(self, event):
        """Dispatches events to the appropriate methods."""
        if event.event_type == EVENT_TYPE_DELETED:
            self.on_deleted(event)
        elif event.event_type == EVENT_TYPE_MODIFIED:
            self.on_modified(event)
        elif event.event_type == EVENT_TYPE_CREATED:
            self.on_created(event)
        elif event.event_type == EVENT_TYPE_MOVED:
            self.on_moved(event)

    def on_moved(self, event):
        """Called when a file or a directory is moved or renamed."""
        pass

    def on_created(self, event):
        """Called when a file or directory is created."""
        pass

    def on_deleted(self, event):
        """Called when a file or directory is deleted."""
        pass

    def on_modified(self, event):
        """Called when a file or directory is modified."""
        pass