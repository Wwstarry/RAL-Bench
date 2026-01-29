# -*- coding: utf-8 -*-
"""
    watchdog.events
    ~~~~~~~~~~~~~~

    File system event classes and event handler base class.
"""

import os
import re
from functools import partial
from fnmatch import fnmatch


class FileSystemEvent:
    """Base class for all file system events."""

    def __init__(self, src_path):
        self._src_path = src_path
        self._is_directory = os.path.isdir(src_path)

    @property
    def src_path(self):
        """Source path of the file system object."""
        return self._src_path

    @property
    def is_directory(self):
        """Whether the event corresponds to a directory or file."""
        return self._is_directory

    def __repr__(self):
        return f"<{self.__class__.__name__}: src_path={self.src_path}, is_directory={self.is_directory}>"


class FileSystemMovedEvent(FileSystemEvent):
    """Event for when a file system object is moved."""

    def __init__(self, src_path, dest_path):
        super().__init__(src_path)
        self._dest_path = dest_path

    @property
    def dest_path(self):
        """Destination path of the file system object."""
        return self._dest_path

    def __repr__(self):
        return (
            f"<{self.__class__.__name__}: src_path={self.src_path}, "
            f"dest_path={self.dest_path}, is_directory={self.is_directory}>"
        )


class FileCreatedEvent(FileSystemEvent):
    """Event for file creation."""


class FileDeletedEvent(FileSystemEvent):
    """Event for file deletion."""


class FileModifiedEvent(FileSystemEvent):
    """Event for file modification."""


class FileMovedEvent(FileSystemMovedEvent):
    """Event for file movement."""


class DirCreatedEvent(FileSystemEvent):
    """Event for directory creation."""


class DirDeletedEvent(FileSystemEvent):
    """Event for directory deletion."""


class DirModifiedEvent(FileSystemEvent):
    """Event for directory modification."""


class DirMovedEvent(FileSystemMovedEvent):
    """Event for directory movement."""


class FileSystemEventHandler:
    """
    Base file system event handler that you can override methods for.
    """

    def dispatch(self, event):
        """Dispatches events to the appropriate methods.

        :param event:
            The event object representing the file system event.
        """
        method_map = {
            FileCreatedEvent: self.on_created,
            FileDeletedEvent: self.on_deleted,
            FileModifiedEvent: self.on_modified,
            FileMovedEvent: self.on_moved,
            DirCreatedEvent: self.on_created,
            DirDeletedEvent: self.on_deleted,
            DirModifiedEvent: self.on_modified,
            DirMovedEvent: self.on_moved,
        }
        handler = method_map.get(event.__class__, self.on_any_event)
        handler(event)

    def on_any_event(self, event):
        """Catch-all event handler.

        :param event:
            The event object representing the file system event.
        """

    def on_created(self, event):
        """Called when a file or directory is created.

        :param event:
            The event object representing the file system event.
        """

    def on_deleted(self, event):
        """Called when a file or directory is deleted.

        :param event:
            The event object representing the file system event.
        """

    def on_modified(self, event):
        """Called when a file or directory is modified.

        :param event:
            The event object representing the file system event.
        """

    def on_moved(self, event):
        """Called when a file or directory is moved or renamed.

        :param event:
            The event object representing the file system event.
        """


class PatternMatchingEventHandler(FileSystemEventHandler):
    """
    Matches given patterns with file paths associated with occurring events.
    """

    def __init__(self, patterns=None, ignore_patterns=None,
                 ignore_directories=False, case_sensitive=False):
        super().__init__()

        self._patterns = patterns
        self._ignore_patterns = ignore_patterns
        self._ignore_directories = ignore_directories
        self._case_sensitive = case_sensitive

    @property
    def patterns(self):
        """Property for the patterns to match files against."""
        return self._patterns

    @property
    def ignore_patterns(self):
        """Property for the patterns to ignore."""
        return self._ignore_patterns

    @property
    def ignore_directories(self):
        """Property for whether to ignore directories or not."""
        return self._ignore_directories

    @property
    def case_sensitive(self):
        """Property for whether patterns should be matched case-sensitively."""
        return self._case_sensitive

    def dispatch(self, event):
        """Dispatches events to the appropriate methods.
        
        :param event:
            The event object representing the file system event.
        """
        if self.ignore_directories and event.is_directory:
            return

        if self._patterns and not self._match_any_pattern(
            event.src_path, self._patterns
        ):
            return

        if self._ignore_patterns and self._match_any_pattern(
            event.src_path, self._ignore_patterns
        ):
            return

        super().dispatch(event)

    def _match_any_pattern(self, path, patterns):
        """Returns True if path matches any of the patterns."""
        if not patterns:
            return False

        for pattern in patterns:
            if self._match_pattern(pattern, path):
                return True
        return False

    def _match_pattern(self, pattern, path):
        """Returns True if the pattern matches the path."""
        if not self.case_sensitive:
            pattern = pattern.lower()
            path = path.lower()
        return fnmatch(path, pattern)


class RegexMatchingEventHandler(PatternMatchingEventHandler):
    """
    Matches given regular expressions with file paths associated with occurring events.
    """

    def _match_pattern(self, pattern, path):
        """Returns True if the pattern matches the path."""
        regex = re.compile(pattern)
        if self.case_sensitive:
            match = regex.match(path)
        else:
            match = regex.match(path.lower())
        return bool(match)