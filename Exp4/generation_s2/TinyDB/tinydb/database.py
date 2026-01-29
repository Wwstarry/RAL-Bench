from __future__ import annotations

from typing import Any, Dict, Optional, Union

from .storages import JSONStorage, Storage
from .table import Table


class TinyDB:
    """
    Lightweight JSON file database.

    Data layout in storage:
    {
      "_default": {
        "1": {...},
        "2": {...}
      },
      "projects": {...}
    }

    Use `db.table("tasks")` etc.
    """

    def __init__(
        self,
        path: str,
        storage: type[Storage] = JSONStorage,
        *,
        indent: Optional[int] = 2,
        sort_keys: bool = True,
        ensure_ascii: bool = False,
    ) -> None:
        self._storage: Storage = storage(
            path, indent=indent, sort_keys=sort_keys, ensure_ascii=ensure_ascii
        )
        self._tables: Dict[str, Table] = {}

    @property
    def storage(self) -> Storage:
        return self._storage

    def table(self, name: str = "_default") -> Table:
        if name not in self._tables:
            self._tables[name] = Table(self._storage, name)
        return self._tables[name]

    # Convenience passthrough to default table:
    def insert(self, document: Dict[str, Any]) -> int:
        return self.table("_default").insert(document)

    def insert_multiple(self, documents: list[Dict[str, Any]]) -> list[int]:
        return self.table("_default").insert_multiple(documents)

    def all(self) -> list[Dict[str, Any]]:
        return self.table("_default").all()

    def search(self, cond) -> list[Dict[str, Any]]:
        return self.table("_default").search(cond)

    def get(self, cond=None, *, doc_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        return self.table("_default").get(cond, doc_id=doc_id)

    def update(self, fields: Union[Dict[str, Any], Any], cond=None, *, doc_ids=None) -> int:
        return self.table("_default").update(fields, cond, doc_ids=doc_ids)

    def remove(self, cond=None, *, doc_ids=None) -> int:
        return self.table("_default").remove(cond, doc_ids=doc_ids)

    def truncate(self) -> None:
        self.table("_default").truncate()

    def close(self) -> None:
        self._storage.close()

    def __enter__(self) -> "TinyDB":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()