"""
File system events and event handlers.
"""
import os
import re
import logging
from abc import ABC, abstractmethod
from typing import Optional, List, Pattern, Any


# Event type constants
EVENT_TYPE_ANY = "any"
EVENT_TYPE_CREATED = "created"
EVENT_TYPE_MODIFIED = "modified"
EVENT_TYPE_DELETED = "deleted"
EVENT_TYPE_MOVED = "moved"
EVENT_TYPE_CLOSED = "closed"
EVENT_TYPE_OPENED = "opened"

EVENT_ANY = (EVENT_TYPE_ANY,)
EVENT_CREATED = (EVENT_TYPE_CREATED,)
EVENT_MODIFIED = (EVENT_TYPE_MODIFIED,)
EVENT_DELETED = (EVENT_TYPE_DELETED,)
EVENT_MOVED = (EVENT_TYPE_MOVED,)
EVENT_CLOSED = (EVENT_TYPE_CLOSED,)
EVENT_OPENED = (EVENT_TYPE_OPENED,)


class FileSystemEvent:
    """Base file system event."""

    def __init__(self, src_path: str, is_directory: bool = False):
        self.src_path = src_path
        self.is_directory = is_directory
        self.event_type: str = ""

    def __str__(self) -> str:
        return f"<{self.__class__.__name__}: src_path={self.src_path!r}>"

    def __repr__(self) -> str:
        return str(self)


class FileCreatedEvent(FileSystemEvent):
    """File created event."""

    def __init__(self, src_path: str):
        super().__init__(src_path, is_directory=False)
        self.event_type = EVENT_TYPE_CREATED


class FileModifiedEvent(FileSystemEvent):
    """File modified event."""

    def __init__(self, src_path: str):
        super().__init__(src_path, is_directory=False)
        self.event_type = EVENT_TYPE_MODIFIED


class FileDeletedEvent(FileSystemEvent):
    """File deleted event."""

    def __init__(self, src_path: str):
        super().__init__(src_path, is_directory=False)
        self.event_type = EVENT_TYPE_DELETED


class DirCreatedEvent(FileSystemEvent):
    """Directory created event."""

    def __init__(self, src_path: str):
        super().__init__(src_path, is_directory=True)
        self.event_type = EVENT_TYPE_CREATED


class DirModifiedEvent(FileSystemEvent):
    """Directory modified event."""

    def __init__(self, src_path: str):
        super().__init__(src_path, is_directory=True)
        self.event_type = EVENT_TYPE_MODIFIED


class DirDeletedEvent(FileSystemEvent):
    """Directory deleted event."""

    def __init__(self, src_path: str):
        super().__init__(src_path, is_directory=True)
        self.event_type = EVENT_TYPE_DELETED


class FileSystemMovedEvent(FileSystemEvent):
    """File system moved event."""

    def __init__(self, src_path: str, dest_path: str, is_directory: bool = False):
        super().__init__(src_path, is_directory)
        self.dest_path = dest_path
        self.event_type = EVENT_TYPE_MOVED

    def __str__(self) -> str:
        return (
            f"<{self.__class__.__name__}: src_path={self.src_path!r}, "
            f"dest_path={self.dest_path!r}>"
        )


class FileMovedEvent(FileSystemMovedEvent):
    """File moved event."""

    def __init__(self, src_path: str, dest_path: str):
        super().__init__(src_path, dest_path, is_directory=False)


class DirMovedEvent(FileSystemMovedEvent):
    """Directory moved event."""

    def __init__(self, src_path: str, dest_path: str):
        super().__init__(src_path, dest_path, is_directory=True)


class FileSystemEventHandler(ABC):
    """
    Base file system event handler. Subclass and override methods to handle events.
    """

    def on_any_event(self, event: FileSystemEvent) -> None:
        """Catch-all event handler."""
        pass

    def on_created(self, event: FileSystemEvent) -> None:
        """Called when a file or directory is created."""
        pass

    def on_modified(self, event: FileSystemEvent) -> None:
        """Called when a file or directory is modified."""
        pass

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Called when a file or directory is deleted."""
        pass

    def on_moved(self, event: FileSystemMovedEvent) -> None:
        """Called when a file or directory is moved."""
        pass

    def on_closed(self, event: FileSystemEvent) -> None:
        """Called when a file is closed after being opened for writing."""
        pass

    def on_opened(self, event: FileSystemEvent) -> None:
        """Called when a file is opened."""
        pass

    def dispatch(self, event: FileSystemEvent) -> None:
        """Dispatch events to the appropriate methods."""
        self.on_any_event(event)

        if event.event_type == EVENT_TYPE_CREATED:
            self.on_created(event)
        elif event.event_type == EVENT_TYPE_MODIFIED:
            self.on_modified(event)
        elif event.event_type == EVENT_TYPE_DELETED:
            self.on_deleted(event)
        elif event.event_type == EVENT_TYPE_MOVED:
            if isinstance(event, FileSystemMovedEvent):
                self.on_moved(event)
        elif event.event_type == EVENT_TYPE_CLOSED:
            self.on_closed(event)
        elif event.event_type == EVENT_TYPE_OPENED:
            self.on_opened(event)


class LoggingEventHandler(FileSystemEventHandler):
    """Logs all the events captured."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        super().__init__()
        self.logger = logger or logging.getLogger(__name__)

    def on_any_event(self, event: FileSystemEvent) -> None:
        self.logger.info(str(event))

    def on_created(self, event: FileSystemEvent) -> None:
        self.logger.info(f"Created: {event.src_path}")

    def on_modified(self, event: FileSystemEvent) -> None:
        self.logger.info(f"Modified: {event.src_path}")

    def on_deleted(self, event: FileSystemEvent) -> None:
        self.logger.info(f"Deleted: {event.src_path}")

    def on_moved(self, event: FileSystemMovedEvent) -> None:
        self.logger.info(f"Moved: {event.src_path} -> {event.dest_path}")


class PatternMatchingEventHandler(FileSystemEventHandler):
    """
    Matches events based on patterns.
    """

    def __init__(
        self,
        patterns: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None,
        ignore_directories: bool = False,
        case_sensitive: bool = False,
    ):
        super().__init__()
        self.patterns = patterns or ["*"]
        self.ignore_patterns = ignore_patterns or []
        self.ignore_directories = ignore_directories
        self.case_sensitive = case_sensitive

        self._patterns = [self._compile_pattern(p) for p in self.patterns]
        self._ignore_patterns = [self._compile_pattern(p) for p in self.ignore_patterns]

    def _compile_pattern(self, pattern: str) -> Pattern:
        """Compile a pattern string to a regex pattern."""
        regex = re.escape(pattern)
        regex = regex.replace(r"\*", ".*").replace(r"\?", ".")
        if not self.case_sensitive:
            return re.compile(f"^{regex}$", re.IGNORECASE)
        return re.compile(f"^{regex}$")

    def _matches(self, path: str) -> bool:
        """Check if path matches any of the patterns."""
        basename = os.path.basename(path)
        # Check ignore patterns first
        for pattern in self._ignore_patterns:
            if pattern.match(basename):
                return False
        # Check inclusion patterns
        for pattern in self._patterns:
            if pattern.match(basename):
                return True
        return False

    def dispatch(self, event: FileSystemEvent) -> None:
        """Dispatch events if they match the patterns."""
        if self.ignore_directories and event.is_directory:
            return
        if self._matches(event.src_path):
            super().dispatch(event)


class RegexMatchingEventHandler(PatternMatchingEventHandler):
    """
    Matches events based on regex patterns.
    """

    def __init__(
        self,
        regexes: Optional[List[str]] = None,
        ignore_regexes: Optional[List[str]] = None,
        ignore_directories: bool = False,
        case_sensitive: bool = False,
    ):
        patterns = None
        ignore_patterns = None
        if regexes:
            patterns = [f"*{r}*" for r in regexes]  # Simple conversion
        if ignore_regexes:
            ignore_patterns = [f"*{r}*" for r in ignore_regexes]
        super().__init__(
            patterns=patterns,
            ignore_patterns=ignore_patterns,
            ignore_directories=ignore_directories,
            case_sensitive=case_sensitive,
        )