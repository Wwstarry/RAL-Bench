from __future__ import annotations

from typing import Any

from .storages import JSONStorage, Storage
from .table import Table


class TinyDB:
    def __init__(
        self,
        path: str,
        *,
        storage: type[Storage] = JSONStorage,
        default_table: str = "_default",
        **storage_kwargs: Any,
    ) -> None:
        self.storage: Storage = storage(path, **storage_kwargs)
        self.default_table_name: str = default_table
        self._closed = False
        self._tables: dict[str, Table] = {}

    def table(self, name: str) -> Table:
        if self._closed:
            raise ValueError("Database is closed")
        if not isinstance(name, str) or name == "":
            raise TypeError("Table name must be a non-empty string")
        t = self._tables.get(name)
        if t is None:
            t = Table(self, name)
            self._tables[name] = t
        return t

    def tables(self) -> set[str]:
        if self._closed:
            raise ValueError("Database is closed")
        data = self.storage.read() or {}
        return {k for k in data.keys() if k != "_meta"}

    def drop_tables(self) -> None:
        if self._closed:
            raise ValueError("Database is closed")
        self.storage.write({})
        self._tables.clear()

    def drop_table(self, name: str) -> None:
        if self._closed:
            raise ValueError("Database is closed")
        data = self.storage.read() or {}
        data.pop(name, None)
        meta = data.get("_meta")
        if isinstance(meta, dict):
            meta.pop(name, None)
            if meta == {}:
                # Keep empty meta if present; either is acceptable.
                data["_meta"] = meta
        self.storage.write(data)
        self._tables.pop(name, None)

    def close(self) -> None:
        if not self._closed:
            self.storage.close()
            self._closed = True

    def __enter__(self) -> "TinyDB":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()