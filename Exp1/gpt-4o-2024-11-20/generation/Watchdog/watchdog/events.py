# watchdog/events.py

class FileSystemEventHandler:
    """
    Base class for handling file system events.
    Subclasses can override the following methods to handle specific events:
    - on_created
    - on_modified
    - on_deleted
    """

    def on_created(self, event):
        """Called when a file or directory is created."""
        pass

    def on_modified(self, event):
        """Called when a file or directory is modified."""
        pass

    def on_deleted(self, event):
        """Called when a file or directory is deleted."""
        pass


class FileSystemEvent:
    """Represents a file system event."""

    def __init__(self, event_type, src_path):
        self.event_type = event_type
        self.src_path = src_path

    def __repr__(self):
        return f"<FileSystemEvent: type={self.event_type}, path={self.src_path}>"