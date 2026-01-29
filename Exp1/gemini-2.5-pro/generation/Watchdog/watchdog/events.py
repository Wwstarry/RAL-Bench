# watchdog/events.py

class FileSystemEvent:
    """Base file system event."""

    def __init__(self, src_path):
        self.src_path = src_path

    @property
    def is_directory(self):
        """True if the event was for a directory; False otherwise."""
        return self._is_directory

    def __repr__(self):
        return (f"<{type(self).__name__}: event_type={self.event_type}, "
                f"src_path={self.src_path!r}, is_directory={self.is_directory}>")


class FileEvent(FileSystemEvent):
    _is_directory = False


class DirEvent(FileSystemEvent):
    _is_directory = True


class FileCreatedEvent(FileEvent):
    event_type = 'created'


class DirCreatedEvent(DirEvent):
    event_type = 'created'


class FileDeletedEvent(FileEvent):
    event_type = 'deleted'


class DirDeletedEvent(DirEvent):
    event_type = 'deleted'


class FileModifiedEvent(FileEvent):
    event_type = 'modified'


class DirModifiedEvent(DirEvent):
    event_type = 'modified'


class FileSystemEventHandler:
    """Base event handler that can be inherited to handle file system events."""

    def dispatch(self, event):
        """Dispatches events to the appropriate methods."""
        self.on_any_event(event)
        if event.event_type == 'created':
            self.on_created(event)
        elif event.event_type == 'deleted':
            self.on_deleted(event)
        elif event.event_type == 'modified':
            self.on_modified(event)

    def on_any_event(self, event):
        """Catch-all event handler.

        :param event:
            The event object representing the file system event.
        """
        pass

    def on_created(self, event):
        """Called when a file or directory is created.

        :param event:
            Event representing file/directory creation.
        """
        pass

    def on_deleted(self, event):
        """Called when a file or directory is deleted.

        :param event:
            Event representing file/directory deletion.
        """
        pass

    def on_modified(self, event):
        """Called when a file or directory is modified.

        :param event:
            Event representing file/directory modification.
        """
        pass