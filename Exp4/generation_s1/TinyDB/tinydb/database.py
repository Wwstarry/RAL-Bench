from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, Union

from .storages import JSONStorage, Storage
from .table import Table


PathLike = Union[str, "Path"]


class TinyDB:
    def __init__(
        self,
        path: PathLike,
        *,
        storage: Type[Storage] = JSONStorage,
        default_table: str = "tasks",
        **storage_kwargs: Any,
    ):
        self.path = Path(path)
        self._storage: Storage = storage(self.path, **storage_kwargs)
        self.default_table = default_table
        self._lock = threading.RLock()

    def table(self, name: str) -> Table:
        return Table(self, name)

    def __getitem__(self, name: str) -> Table:
        return self.table(name)

    def _read(self) -> Dict[str, Any]:
        return self._storage.read()

    def _write(self, data: Dict[str, Any]) -> None:
        self._storage.write(data)

    def _get_table_data(self, data: Dict[str, Any], name: str) -> Dict[str, Any]:
        tbl = data.get(name)
        if tbl is None:
            tbl = {}
            data[name] = tbl
        if not isinstance(tbl, dict):
            raise ValueError(f"Table {name!r} is not a dict in database file")
        return tbl

    def tables(self) -> List[str]:
        with self._lock:
            data = self._read()
            return sorted([k for k, v in data.items() if isinstance(v, dict)])

    def drop_tables(self) -> None:
        with self._lock:
            self._write({})

    def drop_table(self, name: str) -> None:
        with self._lock:
            data = self._read()
            if name in data:
                del data[name]
                self._write(data)

    def close(self) -> None:
        self._storage.close()