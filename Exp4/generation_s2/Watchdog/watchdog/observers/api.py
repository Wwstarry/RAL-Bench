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
    last_snapshot: Dict[str, Tuple[bool, int, int]]  # path -> (is_dir, mtime_ns, size)


def _safe_stat(path: str):
    try:
        return os.stat(path, follow_symlinks=False)
    except FileNotFoundError:
        return None
    except OSError:
        return None


def _is_dir(path: str) -> bool:
    try:
        return os.path.isdir(path)
    except OSError:
        return False


def _iter_paths(root: str, recursive: bool) -> Iterable[str]:
    # Include root itself for directory modification tracking.
    yield root

    if not recursive:
        try:
            with os.scandir(root) as it:
                for entry in it:
                    yield entry.path
        except FileNotFoundError:
            return
        except NotADirectoryError:
            return
        except OSError:
            return
        return

    # Recursive walk
    try:
        for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
            for name in dirnames:
                yield os.path.join(dirpath, name)
            for name in filenames:
                yield os.path.join(dirpath, name)
    except FileNotFoundError:
        return
    except OSError:
        return


def _snapshot(root: str, recursive: bool) -> Dict[str, Tuple[bool, int, int]]:
    snap: Dict[str, Tuple[bool, int, int]] = {}
    for p in _iter_paths(root, recursive):
        st = _safe_stat(p)
        if st is None:
            continue
        isdir = os.path.isdir(p)
        snap[p] = (isdir, getattr(st, "st_mtime_ns", int(st.st_mtime * 1e9)), int(getattr(st, "st_size", 0)))
    return snap


def _normalize_path(p: str) -> str:
    # watchdog typically uses absolute normalized paths
    return os.path.abspath(os.fspath(p))


class Observer:
    """
    Polling-based Observer implementing a minimal watchdog-like API.

    schedule(handler, path, recursive=False)
    start(), stop(), join()
    """

    def __init__(self, timeout: float = 0.1):
        self.timeout = float(timeout) if timeout is not None else 0.1
        self._watches: List[_Watch] = []
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def schedule(self, event_handler: FileSystemEventHandler, path: str, recursive: bool = False):
        wpath = _normalize_path(path)
        watch = _Watch(
            handler=event_handler,
            path=wpath,
            recursive=bool(recursive),
            last_snapshot=_snapshot(wpath, bool(recursive)),
        )
        with self._lock:
            self._watches.append(watch)
        return watch  # watchdog returns an ObservedWatch; tests typically ignore

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="watchdog-observer", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def join(self, timeout: Optional[float] = None) -> None:
        t = self._thread
        if t is None:
            return
        t.join(timeout=timeout)

    def is_alive(self) -> bool:
        t = self._thread
        return bool(t and t.is_alive())

    def _run(self) -> None:
        while not self._stop_event.is_set():
            self._poll_once()
            # Use Event.wait for responsive stop
            self._stop_event.wait(self.timeout)

    def _poll_once(self) -> None:
        with self._lock:
            watches = list(self._watches)
        for watch in watches:
            try:
                self._poll_watch(watch)
            except Exception:
                # Keep observer thread alive even if one watch fails
                continue

    def _poll_watch(self, watch: _Watch) -> None:
        current = _snapshot(watch.path, watch.recursive)
        previous = watch.last_snapshot

        created = [p for p in current.keys() if p not in previous]
        deleted = [p for p in previous.keys() if p not in current]
        potentially_modified = [p for p in current.keys() if p in previous]

        # Emit created events (directories before files for stability)
        created.sort(key=lambda p: (0 if current[p][0] else 1, p))
        for p in created:
            isdir = current[p][0]
            evt = DirCreatedEvent(p) if isdir else FileCreatedEvent(p)
            watch.handler.dispatch(evt)
            # Also treat creation as modification for the parent directory
            parent = os.path.dirname(p)
            if parent and parent in current and parent == watch.path or watch.recursive:
                # best-effort: dispatch DirModifiedEvent for immediate parent if it's tracked
                if parent in current and current[parent][0]:
                    watch.handler.dispatch(DirModifiedEvent(parent))

        # Emit deleted events (files before directories to reduce noisy directory deletes)
        deleted.sort(key=lambda p: (0 if not previous[p][0] else 1, p), reverse=False)
        for p in deleted:
            isdir = previous[p][0]
            evt = DirDeletedEvent(p) if isdir else FileDeletedEvent(p)
            watch.handler.dispatch(evt)
            parent = os.path.dirname(p)
            if parent and parent in current and current[parent][0]:
                watch.handler.dispatch(DirModifiedEvent(parent))

        # Emit modified events based on (mtime_ns, size) change
        for p in potentially_modified:
            cur = current[p]
            prev = previous[p]
            if cur[0] != prev[0]:
                # type changed (file<->dir): treat as delete+create
                if prev[0]:
                    watch.handler.dispatch(DirDeletedEvent(p))
                else:
                    watch.handler.dispatch(FileDeletedEvent(p))
                if cur[0]:
                    watch.handler.dispatch(DirCreatedEvent(p))
                else:
                    watch.handler.dispatch(FileCreatedEvent(p))
                continue

            if cur[1] != prev[1] or cur[2] != prev[2]:
                if cur[0]:
                    watch.handler.dispatch(DirModifiedEvent(p))
                else:
                    watch.handler.dispatch(FileModifiedEvent(p))

        watch.last_snapshot = current