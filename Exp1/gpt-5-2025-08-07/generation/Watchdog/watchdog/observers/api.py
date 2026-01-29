import os
import threading
import time
from typing import Dict, Tuple, List

from watchdog.events import (
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    FileSystemEventHandler,
)


def _stat_signature(path: str) -> Tuple[int, int]:
    """
    Returns a tuple representing the state of a file to detect modifications.
    Uses (mtime_ns, size).
    """
    st = os.stat(path, follow_symlinks=False)
    # st_mtime_ns might not exist on very old Python; fall back gracefully
    mtime_ns = getattr(st, "st_mtime_ns", int(st.st_mtime * 1e9))
    return (int(mtime_ns), int(st.st_size))


def _iter_files(path: str, recursive: bool):
    """
    Iterate over file paths under 'path'. If recursive is True, descend into
    subdirectories. Ignores directories themselves; yields files only.
    """
    if not recursive:
        try:
            with os.scandir(path) as it:
                for entry in it:
                    # Only yield regular files (including symlinks to files)
                    try:
                        if entry.is_file(follow_symlinks=False):
                            yield entry.path
                    except FileNotFoundError:
                        # Entry disappeared between scandir and stat checks
                        continue
        except FileNotFoundError:
            return
        except NotADirectoryError:
            # If path is a file, yield it directly
            if os.path.isfile(path):
                yield path
            return
    else:
        for root, dirs, files in os.walk(path, followlinks=False):
            for name in files:
                yield os.path.join(root, name)


def _snapshot(path: str, recursive: bool) -> Dict[str, Tuple[int, int]]:
    """
    Build a snapshot mapping file path -> (mtime_ns, size) for all files
    under 'path'. Missing or inaccessible files are skipped gracefully.
    """
    snapshot: Dict[str, Tuple[int, int]] = {}
    for fpath in _iter_files(path, recursive):
        try:
            sig = _stat_signature(fpath)
        except (FileNotFoundError, PermissionError, OSError):
            # File may have disappeared or be inaccessible; skip
            continue
        snapshot[fpath] = sig
    return snapshot


class _Watch:
    """
    Internal structure representing a scheduled watch.
    """

    def __init__(self, handler: FileSystemEventHandler, path: str, recursive: bool):
        self.handler = handler
        self.path = os.path.abspath(path)
        self.recursive = bool(recursive)
        self.snapshot: Dict[str, Tuple[int, int]] = _snapshot(self.path, self.recursive)


class Observer:
    """
    A simple polling-based filesystem observer compatible with the core
    parts of watchdog's API required by the test suite.

    Methods:
      - schedule(handler, path, recursive)
      - start(), stop(), join()
    """

    def __init__(self, timeout: float = 0.2):
        """
        Initialize the observer.

        Args:
            timeout: Polling interval in seconds.
        """
        self._timeout = float(timeout)
        self._watches: List[_Watch] = []
        self._lock = threading.RLock()
        self._thread = None  # type: threading.Thread
        self._stopping = threading.Event()
        self._started = threading.Event()

    def schedule(self, handler: FileSystemEventHandler, path: str, recursive: bool = False):
        """
        Schedule monitoring of a directory (or file) at the given path.

        Args:
            handler: A subclass of FileSystemEventHandler that handles events.
            path: Directory path to observe. If a file path is given, the file is observed.
            recursive: If True, monitor subdirectories recursively.
        """
        if not isinstance(handler, FileSystemEventHandler):
            # Allow duck-typed handlers by checking presence of dispatch method
            if not hasattr(handler, "dispatch"):
                raise TypeError("handler must be a FileSystemEventHandler or provide a 'dispatch(event)' method.")

        watch = _Watch(handler, path, recursive)
        with self._lock:
            self._watches.append(watch)

    def start(self):
        """
        Start the observer thread. Subsequent calls have no effect.
        """
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._stopping.clear()
            self._thread = threading.Thread(target=self._run, name="WatchdogPollingObserver", daemon=True)
            self._thread.start()
            self._started.set()

    def stop(self):
        """
        Signal the observer to stop.
        """
        self._stopping.set()
        self._started.clear()

    def join(self, timeout: float = None):
        """
        Wait until the observer thread terminates.

        Args:
            timeout: Optional timeout in seconds.
        """
        t = None
        with self._lock:
            t = self._thread
        if t is not None:
            t.join(timeout)

    def _run(self):
        """
        Background thread loop: Poll for file system changes and dispatch events.
        """
        while not self._stopping.is_set():
            # Copy watches to avoid holding lock during I/O and handler callbacks
            with self._lock:
                watches = list(self._watches)

            for watch in watches:
                try:
                    self._poll_watch(watch)
                except Exception:
                    # Handler or internal error should not stop the loop
                    continue

            # Sleep until next poll cycle or until stopping
            self._stopping.wait(self._timeout)

    def _poll_watch(self, watch: _Watch):
        """
        Compare the current snapshot to the previous one and dispatch events.
        """
        try:
            current = _snapshot(watch.path, watch.recursive)
        except Exception:
            # If the root path itself becomes inaccessible, treat all as deleted.
            current = {}

        previous = watch.snapshot

        # Determine creations, deletions, modifications
        created_paths = [p for p in current.keys() if p not in previous]
        deleted_paths = [p for p in previous.keys() if p not in current]
        modified_paths = [
            p for p in current.keys()
            if (p in previous) and (current[p] != previous[p])
        ]

        # Dispatch events. To provide deterministic ordering, sort paths.
        for p in sorted(created_paths):
            try:
                event = FileCreatedEvent(p)
                watch.handler.dispatch(event)
            except Exception:
                # Continue even if handler raises
                pass

        for p in sorted(modified_paths):
            try:
                event = FileModifiedEvent(p)
                watch.handler.dispatch(event)
            except Exception:
                pass

        for p in sorted(deleted_paths):
            try:
                event = FileDeletedEvent(p)
                watch.handler.dispatch(event)
            except Exception:
                pass

        # Update snapshot after dispatching
        watch.snapshot = current