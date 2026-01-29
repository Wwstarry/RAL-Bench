import os
import time

class FileSystemEvent:
    """
    Base class for all filesystem events.
    """
    def __init__(self, src_path):
        self.src_path = src_path
        self.is_directory = os.path.isdir(src_path)

class FileCreatedEvent(FileSystemEvent):
    pass

class FileModifiedEvent(FileSystemEvent):
    pass

class FileDeletedEvent(FileSystemEvent):
    pass

class FileSystemEventHandler:
    """
    Base event handler class.
    Override methods to handle events.
    """

    def on_created(self, event):
        pass

    def on_modified(self, event):
        pass

    def on_deleted(self, event):
        pass