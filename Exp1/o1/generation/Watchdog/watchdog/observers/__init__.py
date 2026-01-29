import os
import time
import threading

from collections import defaultdict
from watchdog.observers.api import BaseObserver
from watchdog.events import (
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent
)

def _build_snapshot(path, recursive):
    """
    Builds a dictionary snapshot {full_path: (mtime, size, is_dir)} for the given path.
    If recursive is True, walk subdirectories as well.
    """
    snapshot = {}
    if recursive:
        for root, dirs, files in os.walk(path, followlinks=False):
            for name in dirs + files:
                full_path = os.path.join(root, name)
                try:
                    st = os.stat(full_path)
                    snapshot[full_path] = (st.st_mtime, st.st_size, os.path.isdir(full_path))
                except FileNotFoundError:
                    # In case an entry disappears mid-walk
                    pass
    else:
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    try:
                        st = entry.stat()
                        snapshot[entry.path] = (st.st_mtime, st.st_size, entry.is_dir())
                    except FileNotFoundError:
                        pass
        except FileNotFoundError:
            pass
    return snapshot

def _compute_events(old_snapshot, new_snapshot):
    """
    Compare old_snapshot to new_snapshot and yield filesystem events as needed.
    """
    # Check for created or modified
    for path, (mtime, size, is_dir) in new_snapshot.items():
        if path not in old_snapshot:
            # Created
            yield FileCreatedEvent(path, is_dir)
        else:
            old_mtime, old_size, old_is_dir = old_snapshot[path]
            # If time or size changed, we consider it modified
            if (mtime != old_mtime) or (size != old_size):
                yield FileModifiedEvent(path, is_dir)
    # Check for deleted
    for path, (mtime, size, is_dir) in old_snapshot.items():
        if path not in new_snapshot:
            yield FileDeletedEvent(path, is_dir)

class _ScheduledWatch:
    """
    Internal structure to store information about a scheduled watch.
    """
    def __init__(self, path, recursive, event_handler):
        self.path = path
        self.recursive = recursive
        self.event_handler = event_handler
        self.snapshot = _build_snapshot(path, recursive)

class Observer(BaseObserver):
    """
    A naive pure-Python polling-based filesystem observer that monitors changes.
    """

    def __init__(self, timeout=1.0):
        """
        :param timeout: The polling interval in seconds.
        """
        self._timeout = timeout
        self._stopped = True
        self._thread = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._watches = []

    def schedule(self, event_handler, path, recursive=False):
        """
        Schedule path with the provided event handler, either recursively or not.
        """
        watch = _ScheduledWatch(path, recursive, event_handler)
        with self._lock:
            self._watches.append(watch)
        return watch

    def _monitor_loop(self):
        while not self._stop_event.is_set():
            with self._lock:
                for watch in self._watches:
                    new_snapshot = _build_snapshot(watch.path, watch.recursive)
                    events = _compute_events(watch.snapshot, new_snapshot)
                    for event in events:
                        watch.event_handler.dispatch(event)
                    watch.snapshot = new_snapshot
            time.sleep(self._timeout)

    def start(self):
        """
        Start the monitoring thread.
        """
        if not self._stopped:
            return
        self._stopped = False
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """
        Signal the monitoring thread to stop.
        """
        self._stop_event.set()
        self._stopped = True

    def join(self, timeout=None):
        """
        Join the monitoring thread, waiting for it to end or until timeout expires.
        """
        if self._thread is not None:
            self._thread.join(timeout=timeout)