import os

EVENT_TYPE_CREATED = "created"
EVENT_TYPE_DELETED = "deleted"
EVENT_TYPE_MODIFIED = "modified"

class FileSystemEvent:
    """
    Basic filesystem event; it may be specialized by creation, modification, or deletion events.
    """
    def __init__(self, event_type, src_path, is_directory=False):
        self.event_type = event_type
        self.src_path = src_path
        self.is_directory = is_directory

    def __repr__(self):
        return "<FileSystemEvent: type=%s, src_path=%s, is_directory=%s>" % (
            self.event_type,
            self.src_path,
            self.is_directory
        )

class FileCreatedEvent(FileSystemEvent):
    def __init__(self, src_path, is_directory=False):
        super().__init__(EVENT_TYPE_CREATED, src_path, is_directory)

class FileModifiedEvent(FileSystemEvent):
    def __init__(self, src_path, is_directory=False):
        super().__init__(EVENT_TYPE_MODIFIED, src_path, is_directory)

class FileDeletedEvent(FileSystemEvent):
    def __init__(self, src_path, is_directory=False):
        super().__init__(EVENT_TYPE_DELETED, src_path, is_directory)

class FileSystemEventHandler:
    """
    Handles events by dispatching them to the appropriate methods.
    Subclasses can override on_created, on_modified, on_deleted, etc.
    """

    def dispatch(self, event):
        if event.event_type == EVENT_TYPE_CREATED:
            self.on_created(event)
        elif event.event_type == EVENT_TYPE_MODIFIED:
            self.on_modified(event)
        elif event.event_type == EVENT_TYPE_DELETED:
            self.on_deleted(event)

    def on_created(self, event):
        """Called when a file or directory is created."""
        pass

    def on_modified(self, event):
        """Called when a file or directory is modified."""
        pass

    def on_deleted(self, event):
        """Called when a file or directory is deleted."""
        pass