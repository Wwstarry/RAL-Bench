"""
Filesystem event classes and handlers.
"""

import os


class FileSystemEvent:
    """Base class for all filesystem events."""
    
    def __init__(self, src_path, is_directory=False):
        self.src_path = src_path
        self.is_directory = is_directory
    
    @property
    def event_type(self):
        """The type of the event as a string."""
        return self._event_type
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: src_path={self.src_path!r}>"


class FileCreatedEvent(FileSystemEvent):
    """Event representing file creation."""
    _event_type = "created"
    
    def __init__(self, src_path):
        super().__init__(src_path, is_directory=False)


class FileModifiedEvent(FileSystemEvent):
    """Event representing file modification."""
    _event_type = "modified"
    
    def __init__(self, src_path):
        super().__init__(src_path, is_directory=False)


class FileDeletedEvent(FileSystemEvent):
    """Event representing file deletion."""
    _event_type = "deleted"
    
    def __init__(self, src_path):
        super().__init__(src_path, is_directory=False)


class DirCreatedEvent(FileSystemEvent):
    """Event representing directory creation."""
    _event_type = "created"
    
    def __init__(self, src_path):
        super().__init__(src_path, is_directory=True)


class DirModifiedEvent(FileSystemEvent):
    """Event representing directory modification."""
    _event_type = "modified"
    
    def __init__(self, src_path):
        super().__init__(src_path, is_directory=True)


class DirDeletedEvent(FileSystemEvent):
    """Event representing directory deletion."""
    _event_type = "deleted"
    
    def __init__(self, src_path):
        super().__init__(src_path, is_directory=True)


class FileSystemEventHandler:
    """Base class for filesystem event handlers."""
    
    def dispatch(self, event):
        """Dispatches events to the appropriate methods."""
        if event.is_directory:
            if event.event_type == "created":
                self.on_created(event)
            elif event.event_type == "modified":
                self.on_modified(event)
            elif event.event_type == "deleted":
                self.on_deleted(event)
        else:
            if event.event_type == "created":
                self.on_created(event)
            elif event.event_type == "modified":
                self.on_modified(event)
            elif event.event_type == "deleted":
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
    
    def on_moved(self, event):
        """Called when a file or directory is moved."""
        pass