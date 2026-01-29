"""
Light-weight re-implementation of the public *watchdog.events* API sufficient
for the test-suite shipped with this repository.
"""
import os


class FileSystemEvent:
    """
    Base class for all file-system events.

    Parameters
    ----------
    src_path : str
        The path of the file or directory that triggered the event.
    is_directory : bool
        Whether *src_path* is a directory.
    event_type : str
        A short string describing the kind of event (``'created'``,
        ``'modified'`` or ``'deleted'``).
    """

    def __init__(self, src_path: str, is_directory: bool, event_type: str):
        self.src_path = os.path.abspath(src_path)
        self.is_directory = bool(is_directory)
        self.event_type = event_type

    # Convenience helpers -------------------------------------------------
    @property
    def event_type_name(self) -> str:  # pragma: no cover
        return self.__class__.__name__

    def __repr__(self):  # pragma: no cover
        return f"<{self.__class__.__name__} {self.src_path!r}>"


# ---------------------------------------------------------------------------#
# Convenience subclasses replicating the real *watchdog* hierarchy.          #
# ---------------------------------------------------------------------------#
class FileCreatedEvent(FileSystemEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path, False, "created")


class DirCreatedEvent(FileSystemEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path, True, "created")


class FileModifiedEvent(FileSystemEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path, False, "modified")


class DirModifiedEvent(FileSystemEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path, True, "modified")


class FileDeletedEvent(FileSystemEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path, False, "deleted")


class DirDeletedEvent(FileSystemEvent):
    def __init__(self, src_path: str):
        super().__init__(src_path, True, "deleted")


# ---------------------------------------------------------------------------#
# Event handler                                                              #
# ---------------------------------------------------------------------------#
class FileSystemEventHandler:
    """
    Base class for event handlers.

    Users can subclass this and override *on_created*, *on_modified* and
    *on_deleted*.  For convenience a common *dispatch* method is provided
    that routes :class:`FileSystemEvent` objects to the correct callback.
    """

    # --- callbacks (no-op default implementations) -----------------------#
    def on_created(self, event: FileSystemEvent):
        pass

    def on_modified(self, event: FileSystemEvent):
        pass

    def on_deleted(self, event: FileSystemEvent):
        pass

    # -- optional catch-all ----------------------------------------------#
    def on_any_event(self, event: FileSystemEvent):
        """
        Called on every event *before* the specialised callbacks.  Can be
        overridden by subclasses that need a single entry point.
        """
        pass

    # --------------------------------------------------------------------#
    # Public API                                                           #
    # --------------------------------------------------------------------#
    def dispatch(self, event: FileSystemEvent):
        """
        Route *event* to the proper callback.
        """
        # First the catch-all hook.
        self.on_any_event(event)

        # Then the specialised ones.
        if event.event_type == "created":
            self.on_created(event)
        elif event.event_type == "modified":
            self.on_modified(event)
        elif event.event_type == "deleted":
            self.on_deleted(event)