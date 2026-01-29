import threading
import time
import os
import sys

from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
)

class _ObservedWatch:
    def __init__(self, path, handler, recursive):
        self.path = os.path.abspath(path)
        self.handler = handler
        self.recursive = recursive

class Observer:
    def __init__(self, timeout=1.0):
        self._watches = []
        self._lock = threading.Lock()
        self._running = False
        self._thread = None
        self._timeout = timeout

    def schedule(self, handler, path, recursive=False):
        watch = _ObservedWatch(path, handler, recursive)
        with self._lock:
            self._watches.append(watch)

    def start(self):
        with self._lock:
            if self._running:
                return
            self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        with self._lock:
            self._running = False

    def join(self, timeout=None):
        if self._thread is not None:
            self._thread.join(timeout)

    def _run(self):
        # Each watch gets its own snapshot
        snapshots = {}
        while True:
            with self._lock:
                running = self._running
                watches = list(self._watches)
            if not running:
                break
            for watch in watches:
                path = watch.path
                handler = watch.handler
                recursive = watch.recursive
                prev_snapshot = snapshots.get(path)
                try:
                    snapshot = self._snapshot(path, recursive)
                except Exception:
                    continue  # Directory may have been deleted
                if prev_snapshot is None:
                    snapshots[path] = snapshot
                    continue
                # Compare snapshots
                prev_files = prev_snapshot
                curr_files = snapshot

                # Created
                created = curr_files.keys() - prev_files.keys()
                for f in created:
                    event = FileCreatedEvent(f)
                    handler.dispatch(event)
                # Deleted
                deleted = prev_files.keys() - curr_files.keys()
                for f in deleted:
                    event = FileDeletedEvent(f)
                    handler.dispatch(event)
                # Modified
                for f in curr_files.keys() & prev_files.keys():
                    if curr_files[f] != prev_files[f]:
                        event = FileModifiedEvent(f)
                        handler.dispatch(event)
                snapshots[path] = snapshot
            time.sleep(self._timeout)

    def _snapshot(self, path, recursive):
        files = {}
        if not os.path.exists(path):
            return files
        if os.path.isfile(path):
            try:
                stat = os.stat(path)
                files[path] = (stat.st_mtime, stat.st_size)
            except Exception:
                pass
            return files
        # Directory
        if recursive:
            for root, dirs, filenames in os.walk(path):
                for name in dirs:
                    dpath = os.path.join(root, name)
                    try:
                        stat = os.stat(dpath)
                        files[dpath] = (stat.st_mtime, stat.st_size if not os.path.isdir(dpath) else 0)
                    except Exception:
                        continue
                for name in filenames:
                    fpath = os.path.join(root, name)
                    try:
                        stat = os.stat(fpath)
                        files[fpath] = (stat.st_mtime, stat.st_size)
                    except Exception:
                        continue
        else:
            try:
                for entry in os.listdir(path):
                    fpath = os.path.join(path, entry)
                    try:
                        stat = os.stat(fpath)
                        files[fpath] = (stat.st_mtime, stat.st_size if not os.path.isdir(fpath) else 0)
                    except Exception:
                        continue
            except Exception:
                pass
        return files