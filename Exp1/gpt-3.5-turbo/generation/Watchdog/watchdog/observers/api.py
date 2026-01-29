import os
import threading
import time
from collections import defaultdict
from ..events import (
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
)

class Observer:
    """
    Observer monitors filesystem changes and dispatches events to handlers.
    """

    def __init__(self):
        self._lock = threading.RLock()
        self._watches = {}  # path -> (handler, recursive)
        self._running = False
        self._thread = None
        self._snapshot = {}  # path -> (mtime, is_dir)
        self._stop_event = threading.Event()

    def schedule(self, event_handler, path, recursive=False):
        """
        Schedule watching a path with the given event handler.
        """
        path = os.path.abspath(path)
        with self._lock:
            self._watches[path] = (event_handler, recursive)

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
            self._stop_event.clear()
            self._snapshot = self._build_snapshot()
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()

    def stop(self):
        with self._lock:
            if not self._running:
                return
            self._running = False
            self._stop_event.set()

    def join(self, timeout=None):
        thread = None
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join(timeout)

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self._process_events()
            except Exception:
                # Ignore exceptions to keep thread alive
                pass
            time.sleep(1)

    def _build_snapshot(self):
        """
        Build a snapshot of all watched paths and their files.
        Returns a dict: path -> (mtime, is_dir)
        """
        snapshot = {}
        with self._lock:
            for watch_path, (handler, recursive) in self._watches.items():
                if os.path.exists(watch_path):
                    if recursive and os.path.isdir(watch_path):
                        for root, dirs, files in os.walk(watch_path):
                            for name in dirs + files:
                                full_path = os.path.join(root, name)
                                try:
                                    stat = os.stat(full_path)
                                    snapshot[full_path] = (stat.st_mtime, os.path.isdir(full_path))
                                except FileNotFoundError:
                                    # File might have disappeared between os.walk and stat
                                    pass
                    else:
                        try:
                            stat = os.stat(watch_path)
                            snapshot[watch_path] = (stat.st_mtime, os.path.isdir(watch_path))
                        except FileNotFoundError:
                            pass
        return snapshot

    def _process_events(self):
        """
        Detect changes by comparing snapshots and dispatch events.
        """
        new_snapshot = self._build_snapshot()

        # Detect created and modified files
        for path, (mtime, is_dir) in new_snapshot.items():
            if path not in self._snapshot:
                # Created
                self._dispatch_event(path, created=True, is_dir=is_dir)
            else:
                old_mtime, old_is_dir = self._snapshot[path]
                if mtime != old_mtime:
                    # Modified
                    self._dispatch_event(path, modified=True, is_dir=is_dir)

        # Detect deleted files
        for path in self._snapshot:
            if path not in new_snapshot:
                # Deleted
                old_is_dir = self._snapshot[path][1]
                self._dispatch_event(path, deleted=True, is_dir=old_is_dir)

        self._snapshot = new_snapshot

    def _dispatch_event(self, path, created=False, modified=False, deleted=False, is_dir=False):
        """
        Dispatch event to the appropriate handler(s).
        """
        # Find the handler(s) responsible for this path
        with self._lock:
            handlers = []
            for watch_path, (handler, recursive) in self._watches.items():
                # Check if path is under watch_path
                if self._is_path_under_watch(path, watch_path, recursive):
                    handlers.append(handler)

        # Create event object
        if created:
            event = FileCreatedEvent(path)
        elif modified:
            event = FileModifiedEvent(path)
        elif deleted:
            event = FileDeletedEvent(path)
        else:
            return

        # Dispatch event to all handlers
        for handler in handlers:
            try:
                if created:
                    handler.on_created(event)
                elif modified:
                    handler.on_modified(event)
                elif deleted:
                    handler.on_deleted(event)
            except Exception:
                # Ignore exceptions in user handlers
                pass

    def _is_path_under_watch(self, path, watch_path, recursive):
        """
        Check if path is under watch_path considering recursive flag.
        """
        # Normalize paths
        path = os.path.abspath(path)
        watch_path = os.path.abspath(watch_path)

        if path == watch_path:
            return True
        if recursive:
            # Check if path is a subpath of watch_path
            common = os.path.commonpath([path, watch_path])
            return common == watch_path
        else:
            # Non-recursive: only watch the exact path
            return False