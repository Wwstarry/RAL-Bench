# watchdog/observers/api.py

import os
import threading
import time

from watchdog.events import (
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
)


class BaseObserver:
    """Base observer."""

    def __init__(self, timeout=1):
        self._timeout = timeout
        self._stopped_event = threading.Event()
        self._thread = None

    def schedule(self, event_handler, path, recursive=False):
        raise NotImplementedError()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stopped_event.clear()
        self._thread = threading.Thread(target=self.run)
        self._thread.daemon = True
        self._thread.start()

    def stop(self):
        self._stopped_event.set()

    def join(self, timeout=None):
        if self._thread:
            self._thread.join(timeout)

    def run(self):
        raise NotImplementedError("Subclasses must implement run().")


class PollingObserver(BaseObserver):
    """A polling-based observer."""

    def __init__(self, timeout=1):
        super().__init__(timeout=timeout)
        self._lock = threading.Lock()
        self._scheduled_watches = []
        self._snapshots = {}  # Maps watch index to snapshot

    def schedule(self, event_handler, path, recursive=False):
        with self._lock:
            self._scheduled_watches.append((event_handler, path, recursive))

    @staticmethod
    def _take_snapshot(path, recursive):
        snapshot = {}
        try:
            if not os.path.exists(path):
                return snapshot

            if os.path.isdir(path):
                if recursive:
                    for root, _, files in os.walk(path, topdown=True):
                        try:
                            stat = os.stat(root)
                            snapshot[root] = (stat.st_mtime, True)
                        except OSError:
                            continue  # Dir may have been deleted

                        for f in files:
                            file_path = os.path.join(root, f)
                            try:
                                stat = os.stat(file_path)
                                snapshot[file_path] = (stat.st_mtime, False)
                            except OSError:
                                continue  # File may have been deleted
                else:  # Non-recursive
                    try:
                        stat = os.stat(path)
                        snapshot[path] = (stat.st_mtime, True)
                    except OSError:
                        pass  # Dir may have been deleted

                    for name in os.listdir(path):
                        entry_path = os.path.join(path, name)
                        try:
                            stat = os.stat(entry_path)
                            is_dir = os.path.isdir(entry_path)
                            snapshot[entry_path] = (stat.st_mtime, is_dir)
                        except OSError:
                            continue
            else:  # It's a file
                try:
                    stat = os.stat(path)
                    snapshot[path] = (stat.st_mtime, False)
                except OSError:
                    pass
        except OSError:
            pass  # Path does not exist or is not accessible
        return snapshot

    def run(self):
        # Initial snapshots
        with self._lock:
            for i, (_, path, recursive) in enumerate(self._scheduled_watches):
                self._snapshots[i] = self._take_snapshot(path, recursive)

        while not self._stopped_event.wait(self._timeout):
            with self._lock:
                if not self._scheduled_watches:
                    continue

                for i, (handler, path, recursive) in enumerate(self._scheduled_watches):
                    old_snapshot = self._snapshots.get(i, {})
                    new_snapshot = self._take_snapshot(path, recursive)

                    old_paths = set(old_snapshot.keys())
                    new_paths = set(new_snapshot.keys())

                    deleted_paths = old_paths - new_paths
                    created_paths = new_paths - old_paths
                    common_paths = old_paths & new_paths

                    for p in sorted(list(deleted_paths)):
                        _, is_dir = old_snapshot[p]
                        event = DirDeletedEvent(p) if is_dir else FileDeletedEvent(p)
                        handler.dispatch(event)

                    for p in sorted(list(created_paths)):
                        _, is_dir = new_snapshot[p]
                        event = DirCreatedEvent(p) if is_dir else FileCreatedEvent(p)
                        handler.dispatch(event)

                    for p in sorted(list(common_paths)):
                        old_mtime, old_is_dir = old_snapshot[p]
                        new_mtime, new_is_dir = new_snapshot[p]

                        if old_is_dir != new_is_dir:
                            del_event = DirDeletedEvent(p) if old_is_dir else FileDeletedEvent(p)
                            handler.dispatch(del_event)
                            cre_event = DirCreatedEvent(p) if new_is_dir else FileCreatedEvent(p)
                            handler.dispatch(cre_event)
                        elif old_mtime != new_mtime:
                            mod_event = DirModifiedEvent(p) if new_is_dir else FileModifiedEvent(p)
                            handler.dispatch(mod_event)

                    self._snapshots[i] = new_snapshot


Observer = PollingObserver