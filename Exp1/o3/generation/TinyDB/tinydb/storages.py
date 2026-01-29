"""
Storage back-ends.

Only two storages are provided:

    * JSONStorage:  Persists the whole database as one JSON file on disk.
    * MemoryStorage: Keeps everything in memory – handy for testing.

A storage implements *read()* -> data and *write(data)* in a durable way.
"""

from __future__ import annotations

import json
import os
import threading
from typing import Any, Dict


class Storage:
    """
    Base-class for storages.  Sub-classes just have to implement read / write.
    """

    def read(self) -> Dict[str, Any]:
        raise NotImplementedError()

    def write(self, data: Dict[str, Any]) -> None:
        raise NotImplementedError()


class JSONStorage(Storage):
    """
    Store the entire DB as JSON in a single file.  The whole file is read on
    open and written back on each modifying operation.  Because the file is
    small for the intended use-cases (local task manager), this is sufficient.
    """

    def __init__(self, path: str):
        self._path = os.path.abspath(path)
        self._lock = threading.RLock()
        self._data: Dict[str, Any] = {}
        self._load()

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #
    def _load(self) -> None:
        with self._lock:
            if not os.path.exists(self._path):
                self._data = {}
                return
            try:
                with open(self._path, "r", encoding="utf-8") as fp:
                    self._data = json.load(fp)
            except Exception:
                # Corrupted or empty file?  Start over.
                self._data = {}

    def _atomic_write(self, data: Dict[str, Any]) -> None:
        """
        Write *data* atomically – write to a temp file and then move it into
        place so we never end up with a partially written database file.
        """
        tmp_path = f"{self._path}.tmp"
        folder = os.path.dirname(self._path)
        if folder and not os.path.isdir(folder):
            os.makedirs(folder, exist_ok=True)

        with open(tmp_path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, indent=2)

        os.replace(tmp_path, self._path)

    # --------------------------------------------------------------------- #
    # Public API required by TinyDB
    # --------------------------------------------------------------------- #
    def read(self) -> Dict[str, Any]:
        with self._lock:
            # return a *copy* so users do not mutate internals inadvertently
            return json.loads(json.dumps(self._data))

    def write(self, data: Dict[str, Any]) -> None:
        with self._lock:
            self._atomic_write(data)
            # keep in-memory copy in sync
            self._data = json.loads(json.dumps(data))


class MemoryStorage(Storage):
    """
    Simple in-memory storage – never touches disk.  Useful for tests.
    """

    def __init__(self):
        self._data: Dict[str, Any] = {}

    def read(self) -> Dict[str, Any]:
        # Return a deep copy for safety
        return json.loads(json.dumps(self._data))

    def write(self, data: Dict[str, Any]) -> None:
        self._data = json.loads(json.dumps(data))