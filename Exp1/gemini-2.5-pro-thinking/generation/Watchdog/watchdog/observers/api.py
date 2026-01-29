import os
import stat
import threading
from collections import namedtuple

from watchdog.events import (
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
)

ObservedWatch = namedtuple('ObservedWatch', 'path, event_handler, recursive')


class Observer(threading.Thread):
    """
    Observer thread that schedules watches and dispatches events.
    This is a polling-based implementation.
    """

    def __init__(self, timeout=1):
        super().__init__()
        self._watches = set()
        self._lock = threading.RLock()
        self._stopped_event = threading.Event()
        self.timeout = timeout
        self._snapshots = {}

    def schedule(self, event_handler, path, recursive=False):
        """Schedules watching a path for events."""
        with self._lock:
            path = os.path.realpath(str(path))
            watch = ObservedWatch(path, event_handler, recursive)
            self._watches.add(watch)
            if self.is_alive():
                self._snapshots[watch] = self._take_snapshot(watch)
        return watch

    def unschedule(self, watch):
        """Unschedules a watch."""
        with self._lock:
            self._watches.discard(watch)
            self._snapshots.pop(watch, None)

    def start(self):
        """Starts the observer thread."""
        with self._lock:
            if not self._snapshots:
                for watch in self._watches:
                    self._snapshots[watch] = self._take_snapshot(watch)
        super().start()

    def stop(self):
        """Stops the observer thread."""
        self._stopped_event.set()

    def join(self, timeout=None):
        """Waits for the observer thread to finish."""
        super().join(timeout)

    def run(self):
        """The observer thread entry point."""
        while not self._stopped_event.wait(self.timeout):
            with self._lock:
                watches = list(self._watches)

            for watch in watches:
                try:
                    if watch not in self._snapshots:
                        self._snapshots[watch] = self._take_snapshot(watch)
                        continue

                    old_snapshot = self._snapshots[watch]
                    new_snapshot = self._take_snapshot(watch)
                    self._snapshots[watch] = new_snapshot

                    if old_snapshot is None:
                        self._compare_snapshots(watch, {}, new_snapshot)
                    else:
                        self._compare_snapshots(watch, old_snapshot, new_snapshot)

                except (OSError, FileNotFoundError):
                    if self._snapshots.get(watch) is not None:
                        handler = watch.event_handler
                        event = DirDeletedEvent(watch.path)
                        handler.dispatch(event)
                        self._snapshots[watch] = None

    @staticmethod
    def _take_snapshot(watch):
        snapshot = {}
        try:
            stat_info = os.stat(watch.path)
            snapshot[watch.path] = (stat_info.st_mtime, True)

            if watch.recursive:
                for root, dirs, files in os.walk(watch.path, topdown=True):
                    for d in dirs:
                        path = os.path.join(root, d)
                        try:
                            stat_info = os.stat(path)
                            snapshot[path] = (stat_info.st_mtime, True)
                        except (FileNotFoundError, OSError):
                            continue
                    for f in files:
                        path = os.path.join(root, f)
                        try:
                            stat_info = os.stat(path)
                            snapshot[path] = (stat_info.st_mtime, False)
                        except (FileNotFoundError, OSError):
                            continue
            else:
                for name in os.listdir(watch.path):
                    path = os.path.join(watch.path, name)
                    try:
                        stat_info = os.stat(path)
                        is_dir = stat.S_ISDIR(stat_info.st_mode)
                        snapshot[path] = (stat_info.st_mtime, is_dir)
                    except (FileNotFoundError, OSError):
                        continue
        except (FileNotFoundError, OSError):
            return {}
        return snapshot

    def _compare_snapshots(self, watch, old_snapshot, new_snapshot):
        handler = watch.event_handler

        old_paths = set(old_snapshot.keys())
        new_paths = set(new_snapshot.keys())

        created_paths = new_paths - old_paths
        deleted_paths = old_paths - new_paths
        common_paths = new_paths & old_paths

        for path in sorted(list(created_paths)):
            _mtime, is_dir = new_snapshot[path]
            if is_dir:
                handler.dispatch(DirCreatedEvent(path))
            else:
                handler.dispatch(FileCreatedEvent(path))

        for path in sorted(list(deleted_paths), reverse=True):
            _mtime, is_dir = old_snapshot[path]
            if is_dir:
                handler.dispatch(DirDeletedEvent(path))
            else:
                handler.dispatch(FileDeletedEvent(path))

        for path in common_paths:
            old_mtime, _old_is_dir = old_snapshot[path]
            new_mtime, is_dir = new_snapshot[path]

            if old_mtime != new_mtime:
                if is_dir:
                    handler.dispatch(DirModifiedEvent(path))
                else:
                    handler.dispatch(FileModifiedEvent(path))