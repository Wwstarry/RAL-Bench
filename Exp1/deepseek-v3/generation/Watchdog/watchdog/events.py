"""
File system events and event handlers.
"""

import os


class FileSystemEvent:
    """Base file system event class."""
    
    def __init__(self, src_path):
        self.src_path = src_path
        self.is_directory = os.path.isdir(src_path) if os.path.exists(src_path) else False
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: src_path='{self.src_path}'>"


class FileCreatedEvent(FileSystemEvent):
    """File created event."""
    pass


class FileModifiedEvent(FileSystemEvent):
    """File modified event."""
    pass


class FileDeletedEvent(FileSystemEvent):
    """File deleted event."""
    pass


class FileMovedEvent(FileSystemEvent):
    """File moved event."""
    
    def __init__(self, src_path, dest_path):
        super().__init__(src_path)
        self.dest_path = dest_path
    
    def __repr__(self):
        return f"<{self.__class__.__name__}: src_path='{self.src_path}', dest_path='{self.dest_path}'>"


class FileSystemEventHandler:
    """
    Base file system event handler that can be overridden to handle
    file system events.
    """
    
    def on_any_event(self, event):
        """Catch-all event handler."""
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
    
    def on_moved(self, event):
        """Called when a file or directory is moved or renamed."""
        pass
    
    def dispatch(self, event):
        """Dispatch events to the appropriate methods."""
        self.on_any_event(event)
        
        if isinstance(event, FileCreatedEvent):
            self.on_created(event)
        elif isinstance(event, FileModifiedEvent):
            self.on_modified(event)
        elif isinstance(event, FileDeletedEvent):
            self.on_deleted(event)
        elif isinstance(event, FileMovedEvent):
            self.on_moved(event)