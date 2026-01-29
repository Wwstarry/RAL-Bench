from __future__ import annotations

import os
import threading
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

from watchdog.events import (
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileSystemEventHandler,
)


@dataclass
class _Watch:
    handler: FileSystemEventHandler
    path: str
    recursive: bool


def _is_under(path: str, root: str) -> bool:
    # Normalize and compare with commonpath
    try:
        path_n = os.path.abspath(path)
        root_n = os.path.abspath(root)
        return os.path.commonpath([path_n, root_n]) == root_n
    except Exception:
        return False


def _scan_tree(root: str, recursive: bool) -> Dict[str, Tuple[bool, Optional[int], Optional[float]]]:
    """
    Return mapping: path -> (is_dir, size, mtime)

    For directories, size is None and mtime is directory mtime.
    For files, size and mtime are from stat.
    """
    result: Dict[str, Tuple[bool, Optional[int], Optional[float]]] = {}

    root = os.path.abspath(root)
    try:
        st = os.stat(root)
        result[root] = (True, None, float(st.st_mtime))
    except FileNotFoundError:
        return result

    if not recursive:
        try:
            with os.scandir(root) as it:
                for entry in it:
                    p = entry.path
                    try:
                        st = entry.stat(follow_symlinks=False)
                    except FileNotFoundError:
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        result[os.path.abspath(p)] = (True, None, float(st.st_mtime))
                    else:
                        result[os.path.abspath(p)] = (False, int(st.st_size), float(st.st_mtime))
        except FileNotFoundError:
            pass
        return result

    for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
        dirpath_abs = os.path.abspath(dirpath)
        try:
            st = os.stat(dirpath_abs)
            result[dirpath_abs] = (True, None, float(st.st_mtime))
        except FileNotFoundError:
            continue

        # Include directories discovered by walk
        for d in dirnames:
            p = os.path.abspath(os.path.join(dirpath_abs, d))
            try:
                st = os.stat(p)
                result[p] = (True, None, float(st.st_mtime))
            except FileNotFoundError:
                continue
        for f in filenames:
            p = os.path.abspath(os.path.join(dirpath_abs, f))
            try:
                st = os.stat(p)
                result[p] = (False, int(st.st_size), float(st.st_mtime))
            except FileNotFoundError:
                continue

    return result


class Observer:
    """
    Polling-based observer providing a subset of watchdog.observers.Observer.

    schedule(handler, path, recursive)
    start(), stop(), join()
    """

    def __init__(self, timeout: float = 0.1):
        self._timeout = float(timeout)
        self._watches: List[_Watch] = []
        self._lock = threading.RLock()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Each watch has a snapshot mapping path -> (is_dir, size, mtime)
        self._snapshots: List[Dict[str, Tuple[bool, Optional[int], Optional[float]]]] = []

    def schedule(self, event_handler: FileSystemEventHandler, path: str, recursive: bool = False):
        path = os.path.abspath(os.fspath(path))
        watch = _Watch(handler=event_handler, path=path, recursive=bool(recursive))
        with self._lock:
            self._watches.append(watch)
            self._snapshots.append(_scan_tree(path, watch.recursive))
        return watch  # watchdog returns an ObservedWatch-like object; tests often ignore.

    def start(self) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            self._thread = threading.Thread(target=self._run, name="watchdog-observer", daemon=True)
            self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def join(self, timeout: Optional[float] = None) -> None:
        t = self._thread
        if t is not None:
            t.join(timeout=timeout)

    def is_alive(self) -> bool:
        t = self._thread
        return bool(t and t.is_alive())

    def _emit_created(self, watch: _Watch, path: str, is_dir: bool) -> None:
        if is_dir:
            watch.handler.dispatch(DirCreatedEvent(path))
        else:
            watch.handler.dispatch(FileCreatedEvent(path))

    def _emit_deleted(self, watch: _Watch, path: str, is_dir: bool) -> None:
        if is_dir:
            watch.handler.dispatch(DirDeletedEvent(path))
        else:
            watch.handler.dispatch(FileDeletedEvent(path))

    def _emit_modified(self, watch: _Watch, path: str, is_dir: bool) -> None:
        if is_dir:
            watch.handler.dispatch(DirModifiedEvent(path))
        else:
            watch.handler.dispatch(FileModifiedEvent(path))

    def _diff_and_dispatch(
        self,
        watch: _Watch,
        old: Dict[str, Tuple[bool, Optional[int], Optional[float]]],
        new: Dict[str, Tuple[bool, Optional[int], Optional[float]]],
    ) -> None:
        old_keys = set(old.keys())
        new_keys = set(new.keys())

        created = new_keys - old_keys
        deleted = old_keys - new_keys
        common = old_keys & new_keys

        # Dispatch created: parents first for nicer ordering (dirs before files)
        for p in sorted(created, key=lambda x: (x.count(os.sep), x)):
            is_dir, _, _ = new[p]
            # Ensure the created item is within watch path (defensive)
            if _is_under(p, watch.path):
                self._emit_created(watch, p, is_dir)

        # Dispatch modified for common items
        for p in sorted(common):
            is_dir_o, size_o, mtime_o = old[p]
            is_dir_n, size_n, mtime_n = new[p]
            if is_dir_o != is_dir_n:
                # Treat as delete + create
                if _is_under(p, watch.path):
                    self._emit_deleted(watch, p, is_dir_o)
                    self._emit_created(watch, p, is_dir_n)
                continue

            # Polling heuristic: modification if mtime or size differs (files),
            # or mtime differs (dirs).
            modified = False
            if is_dir_n:
                if mtime_o != mtime_n:
                    modified = True
            else:
                if mtime_o != mtime_n or size_o != size_n:
                    modified = True

            if modified and _is_under(p, watch.path):
                self._emit_modified(watch, p, is_dir_n)

        # Dispatch deleted: deeper paths first (files before parent dirs)
        for p in sorted(deleted, key=lambda x: (-x.count(os.sep), x)):
            is_dir, _, _ = old[p]
            if _is_under(p, watch.path):
                self._emit_deleted(watch, p, is_dir)

    def _run(self) -> None:
        while not self._stop_event.is_set():
            # Copy watch list under lock; do scanning outside to reduce contention.
            with self._lock:
                watches = list(self._watches)
                snapshots = list(self._snapshots)

            new_snapshots: List[Dict[str, Tuple[bool, Optional[int], Optional[float]]]] = []
            for i, watch in enumerate(watches):
                old = snapshots[i] if i < len(snapshots) else {}
                new = _scan_tree(watch.path, watch.recursive)
                try:
                    self._diff_and_dispatch(watch, old, new)
                except Exception:
                    # Best-effort; never kill thread in tests due to handler errors.
                    pass
                new_snapshots.append(new)

            with self._lock:
                # Update snapshots for existing watches. If schedule() was called
                # concurrently, extend snapshots as needed.
                self._snapshots[: len(new_snapshots)] = new_snapshots

            time.sleep(self._timeout)