"""
Database handle coordinating multiple tables and persistence.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from .storages import JSONStorage, MemoryStorage, Storage
from .table import Table


class TinyDB:
    """
    A minimal TinyDB clone.  Example:

        from tinydb import TinyDB, Query

        db = TinyDB("tasks.json")
        Task = Query()

        tasks = db.table("tasks")
        tasks.insert({"title": "write docs", "status": "todo", "project": "tiny"})

        print(tasks.search(Task.status == "todo"))
    """

    def __init__(self, path: str | None = None, storage: Storage | None = None):
        """
        Either *path* (string) or *storage* instance must be supplied:

            TinyDB("mydb.json")
            TinyDB(storage=MemoryStorage())
        """
        if storage is None and path is None:
            raise ValueError("Either 'path' or 'storage' must be provided")

        if storage is None:
            storage = JSONStorage(path)  # type: ignore[arg-type]

        self._storage: Storage = storage
        self._data: Dict = self._storage.read() or {}
        self._tables: Dict[str, Table] = {}

    # -------------------------------------------------------------- #
    # Table management
    # -------------------------------------------------------------- #
    def table(self, name: str = "_default") -> Table:
        if name not in self._tables:
            self._tables[name] = Table(self, name)
        return self._tables[name]

    # Shortcut to default table
    def __getattr__(self, item):
        if item == "table" or item.startswith("_"):
            return super().__getattribute__(item)
        # Allow attribute access as table name: db.tasks
        return self.table(item)

    # -------------------------------------------------------------- #
    # Direct wrappers for default table for convenience
    # -------------------------------------------------------------- #
    def insert(self, doc):
        return self.table().insert(doc)

    def all(self):
        return self.table().all()

    def search(self, cond):
        return self.table().search(cond)

    def get(self, cond):
        return self.table().get(cond)

    def update(self, fields_or_func, cond):
        return self.table().update(fields_or_func, cond)

    def remove(self, cond):
        return self.table().remove(cond)

    def count(self, cond=None):
        return self.table().count(cond)

    # -------------------------------------------------------------- #
    # Persistence handling
    # -------------------------------------------------------------- #
    def _flush(self):
        """Write current data to storage."""
        self._storage.write(self._data)

    def close(self):
        """Flush changes and close the storage if needed."""
        self._flush()
        # Storage currently does not hold open resources, but we add hook
        if hasattr(self._storage, "close"):
            self._storage.close()  # type: ignore[attr-defined]

    # -------------------------------------------------------------- #
    # Convenience
    # -------------------------------------------------------------- #
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()