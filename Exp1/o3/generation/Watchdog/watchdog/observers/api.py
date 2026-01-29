"""
A **very** small subset of watchdog's observer API implemented with a simple
polling thread.

It is *not* intended for production use but is sufficient for the unit tests
that accompany this repository.
"""
from __future__ import annotations

import os
import threading
import time
from typing import Dict, List, Tuple

from ..events import (
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileSystemEventHandler,
)


# ---------------------------------------------------------------------------#
# Helper utilities                                                           #
# ---------------------------------------------------------------------------#
def _iter_paths(root: str, recursive: bool):
    """
    Yield ``(path, is_directory)`` pairs under *root*.

    The root directory itself is **not** yielded, only its contents.
    """
    try:
        if recursive:
            for dirname, dirnames, filenames in os.walk(root):
                # Directories first
                for d in dirnames:
                    p = os.path.join(dirname, d)
                    yield p, True
                # Then files
                for f in filenames:
                    p = os.path.join(dirname, f)
                    yield p, False
        else:
            for name in os.listdir(root):
                p = os.path.join(root, name)
                is_dir = os.path.isdir(p)
                yield p, is_dir
    except FileNotFoundError:
        # The monitored path might have been removed.
        return


def _take_snapshot(root: str, recursive: bool) -> Dict[str, Tuple[bool, float, int]]:
    """
    Return a mapping: path → (is_directory, mtime, size)

    For directories *size* is always 0.  The function is tolerant to races
    (file deleted between listdir & stat); such paths are silently skipped.
    """
    snapshot: Dict[str, Tuple[bool, float, int]] = {}
    for path, is_dir in _iter_paths(root, recursive):
        try:
            stat = os.stat(path)
            mtime = stat.st_mtime
            size = 0 if is_dir else stat.st_size
            snapshot[path] = (is_dir, mtime, size)
        except FileNotFoundError:
            continue
    return snapshot


# ---------------------------------------------------------------------------#
# Core implementation                                                        #
# ---------------------------------------------------------------------------#
class _Watch:
    """
    Internal book-keeping object returned by :pymeth:`Observer.schedule`.
    """

    def __init__(self, path: str, recursive: bool, handler: FileSystemEventHandler):
        self.path = os.path.abspath(path)
        self.recursive = recursive
        self.handler = handler
        self.snapshot: Dict[str, Tuple[bool, float, int]] = _take_snapshot(
            self.path, self.recursive
        )

    # Minor helpers to generate the correct event objects -----------------#
    @staticmethod
    def _create_event(is_dir: bool, event_type: str, path: str):
        if event_type == "created":
            return DirCreatedEvent(path) if is_dir else FileCreatedEvent(path)
        elif event_type == "modified":
            return DirModifiedEvent(path) if is_dir else FileModifiedEvent(path)
        elif event_type == "deleted":
            return DirDeletedEvent(path) if is_dir else FileDeletedEvent(path)
        else:  # pragma: no cover
            raise ValueError(event_type)


class Observer:
    """
    Very small clone of ``watchdog.observers.Observer`` using polling.

    Only the subset of the original API required by our tests is implemented.
    """

    def __init__(self, timeout: float = 0.1):
        self._poll_interval = float(timeout)
        self._watches: List[_Watch] = []
        self._running = threading.Event()
        self._thread: threading.Thread | None = None

    # --------------------------------------------------------------------#
    # Public API                                                           #
    # --------------------------------------------------------------------#
    def schedule(
        self, handler: FileSystemEventHandler, path: str, recursive: bool = False
    ) -> _Watch:
        """
        Start watching *path* and dispatch events to *handler*.

        Returns
        -------
        _Watch
            A lightweight watch object representing the request.  The tests do
            not utilise it, but returning it mirrors the upstream API.
        """
        if not isinstance(handler, FileSystemEventHandler):
            raise TypeError("handler must be an instance of FileSystemEventHandler")

        watch = _Watch(path=path, recursive=recursive, handler=handler)
        self._watches.append(watch)
        return watch

    def start(self):
        """
        Start the internal polling thread.
        """
        if self._thread and self._thread.is_alive():
            return  # already running

        self._running.set()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        """
        Signal the polling thread to terminate.
        """
        self._running.clear()

    def join(self, timeout: float | None = None):
        """
        Wait until the polling thread finishes.
        """
        if self._thread:
            self._thread.join(timeout=timeout)

    # --------------------------------------------------------------------#
    # Internal worker                                                      #
    # --------------------------------------------------------------------#
    def _run(self):
        """
        Main polling loop executed in a background thread.
        """
        while self._running.is_set():
            for watch in list(self._watches):  # shallow copy – handlers may alter list
                self._poll_watch(watch)
            time.sleep(self._poll_interval)

    # Core diffing logic --------------------------------------------------#
    def _poll_watch(self, watch: _Watch):
        new_snapshot = _take_snapshot(watch.path, watch.recursive)

        old_paths = set(watch.snapshot.keys())
        new_paths = set(new_snapshot.keys())

        # Created ---------------------------------------------------------#
        for path in new_paths - old_paths:
            is_dir, _, _ = new_snapshot[path]
            event = watch._create_event(is_dir, "created", path)
            watch.handler.dispatch(event)

        # Deleted ---------------------------------------------------------#
        for path in old_paths - new_paths:
            is_dir, _, _ = watch.snapshot[path]
            event = watch._create_event(is_dir, "deleted", path)
            watch.handler.dispatch(event)

        # Modified --------------------------------------------------------#
        for path in old_paths & new_paths:
            is_dir, mtime_old, size_old = watch.snapshot[path]
            _, mtime_new, size_new = new_snapshot[path]

            if (mtime_new != mtime_old) or (size_new != size_old):
                # Avoid flooding directory events unless their mtime changed.
                event = watch._create_event(is_dir, "modified", path)
                watch.handler.dispatch(event)

        # Update stored snapshot
        watch.snapshot = new_snapshot