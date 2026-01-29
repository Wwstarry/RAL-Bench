"""
Filesystem event classes and utilities.
"""

import os
from pathlib import Path
from typing import Optional


class FileSystemEvent:
    """Base class for filesystem events."""
    
    EVENT_TYPE_CREATED = "created"
    EVENT_TYPE_MODIFIED = "modified"
    EVENT_TYPE_DELETED = "deleted"
    EVENT_TYPE_MOVED = "moved"
    
    def __init__(self, src_path: str, is_directory: bool = False):
        """
        Initialize a filesystem event.
        
        Args:
            src_path: Path to the file or directory that triggered the event.
            is_directory: Whether the path is a directory.
        """
        self.src_path = src_path
        self.is_directory = is_directory
    
    @property
    def event_type(self) -> str:
        """Return the type of event."""
        raise NotImplementedError
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(src_path={self.src_path!r}, is_directory={self.is_directory})"


class CreatedEvent(FileSystemEvent):
    """Event fired when a file or directory is created."""
    
    @property
    def event_type(self) -> str:
        return self.EVENT_TYPE_CREATED


class ModifiedEvent(FileSystemEvent):
    """Event fired when a file or directory is modified."""
    
    @property
    def event_type(self) -> str:
        return self.EVENT_TYPE_MODIFIED


class DeletedEvent(FileSystemEvent):
    """Event fired when a file or directory is deleted."""
    
    @property
    def event_type(self) -> str:
        return self.EVENT_TYPE_DELETED


class MovedEvent(FileSystemEvent):
    """Event fired when a file or directory is moved or renamed."""
    
    def __init__(self, src_path: str, dest_path: str, is_directory: bool = False):
        """
        Initialize a moved event.
        
        Args:
            src_path: Original path.
            dest_path: New path.
            is_directory: Whether the path is a directory.
        """
        super().__init__(src_path, is_directory)
        self.dest_path = dest_path
    
    @property
    def event_type(self) -> str:
        return self.EVENT_TYPE_MOVED