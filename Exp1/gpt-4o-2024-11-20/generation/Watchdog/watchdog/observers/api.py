# watchdog/observers/api.py

import os
import time
import threading
from watchdog.events import FileSystemEvent, FileSystemEventHandler


class Observer:
    """
    A pure Python implementation of a file system observer.
    """

    def __init__(self):
        self._handlers = []
        self._running = False
        self._lock = threading.Lock()
        self._thread = None

    def schedule(self, handler, path, recursive=False):
        """
        Schedules a handler for monitoring a specific path.
        """
        if not isinstance(handler, FileSystemEventHandler):
            raise TypeError("Handler must be an instance of FileSystemEventHandler")
        with self._lock:
            self._handlers.append((handler, path, recursive))

    def start(self):
        """
        Starts the observer thread.
        """
        with self._lock:
            if self._running:
                raise RuntimeError("Observer is already running")
            self._running = True
            self._thread = threading.Thread(target=self._monitor)
            self._thread.daemon = True
            self._thread.start()

    def stop(self):
        """
        Stops the observer thread.
        """
        with self._lock:
            self._running = False

    def join(self, timeout=None):
        """
        Waits for the observer thread to finish.
        """
        if self._thread:
            self._thread.join(timeout)

    def _monitor(self):
        """
        Monitors the file system for changes.
        """
        previous_snapshots = {}
        while self._running:
            with self._lock:
                for handler, path, recursive in self._handlers:
                    current_snapshot = self._snapshot(path, recursive)
                    previous_snapshot = previous_snapshots.get(path, {})
                    self._dispatch_events(handler, previous_snapshot, current_snapshot)
                    previous_snapshots[path] = current_snapshot
            time.sleep(1)

    def _snapshot(self, path, recursive):
        """
        Takes a snapshot of the file system at the given path.
        """
        snapshot = {}
        for root, dirs, files in os.walk(path):
            for name in files + dirs:
                full_path = os.path.join(root, name)
                try:
                    snapshot[full_path] = os.stat(full_path).st_mtime
                except FileNotFoundError:
                    pass
            if not recursive:
                break
        return snapshot

    def _dispatch_events(self, handler, previous_snapshot, current_snapshot):
        """
        Dispatches events based on the differences between snapshots.
        """
        previous_paths = set(previous_snapshot.keys())
        current_paths = set(current_snapshot.keys())

        # Detect created files/directories
        for created_path in current_paths - previous_paths:
            event = FileSystemEvent("created", created_path)
            handler.on_created(event)

        # Detect deleted files/directories
        for deleted_path in previous_paths - current_paths:
            event = FileSystemEvent("deleted", deleted_path)
            handler.on_deleted(event)

        # Detect modified files/directories
        for common_path in previous_paths & current_paths:
            if previous_snapshot[common_path] != current_snapshot[common_path]:
                event = FileSystemEvent("modified", common_path)
                handler.on_modified(event)