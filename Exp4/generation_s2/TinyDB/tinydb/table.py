from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, Union

from .queries import Query
from .storages import Storage


class Document(dict):
    """
    A dict with an attached doc_id.
    """

    def __init__(self, *args, doc_id: int, **kwargs):
        super().__init__(*args, **kwargs)
        self.doc_id = doc_id

    def copy(self) -> "Document":  # type: ignore[override]
        return Document(super().copy(), doc_id=self.doc_id)


UpdateSpec = Union[Dict[str, Any], Callable[[Dict[str, Any]], None]]


@dataclass(frozen=True)
class QueryStats:
    matched: int
    returned: int


class Table:
    def __init__(self, storage: Storage, name: str) -> None:
        self._storage = storage
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def _read_table(self) -> Dict[str, Dict[str, Any]]:
        data = self._storage.read()
        table = data.get(self._name, {})
        if not isinstance(table, dict):
            return {}
        return table  # {str(doc_id): document}

    def _write_table(self, table: Dict[str, Dict[str, Any]]) -> None:
        data = self._storage.read()
        data[self._name] = table
        self._storage.write(data)

    def _next_id(self, table: Dict[str, Dict[str, Any]]) -> int:
        if not table:
            return 1
        try:
            return max(int(k) for k in table.keys()) + 1
        except ValueError:
            # If keys are not integers for some reason, reset numbering
            return 1

    def _iter_docs(self, table: Dict[str, Dict[str, Any]]) -> Iterator[Document]:
        for k, v in table.items():
            try:
                doc_id = int(k)
            except ValueError:
                continue
            if isinstance(v, dict):
                yield Document(v, doc_id=doc_id)

    def insert(self, document: Dict[str, Any]) -> int:
        if not isinstance(document, dict):
            raise TypeError("document must be a dict")

        table = self._read_table()
        doc_id = self._next_id(table)
        table[str(doc_id)] = dict(document)
        self._write_table(table)
        return doc_id

    def insert_multiple(self, documents: List[Dict[str, Any]]) -> List[int]:
        table = self._read_table()
        ids: List[int] = []
        for doc in documents:
            if not isinstance(doc, dict):
                raise TypeError("each document must be a dict")
            doc_id = self._next_id(table)
            table[str(doc_id)] = dict(doc)
            ids.append(doc_id)
        self._write_table(table)
        return ids

    def all(self) -> List[Document]:
        table = self._read_table()
        return list(self._iter_docs(table))

    def get(self, cond: Optional[Query] = None, *, doc_id: Optional[int] = None) -> Optional[Document]:
        table = self._read_table()
        if doc_id is not None:
            v = table.get(str(doc_id))
            if isinstance(v, dict):
                return Document(v, doc_id=doc_id)
            return None

        if cond is None:
            raise ValueError("either cond or doc_id must be provided")

        for doc in self._iter_docs(table):
            if cond(doc):
                return doc
        return None

    def search(self, cond: Query) -> List[Document]:
        table = self._read_table()
        return [doc for doc in self._iter_docs(table) if cond(doc)]

    def contains(self, cond: Optional[Query] = None, *, doc_id: Optional[int] = None) -> bool:
        return self.get(cond, doc_id=doc_id) is not None

    def update(
        self,
        fields: UpdateSpec,
        cond: Optional[Query] = None,
        *,
        doc_ids: Optional[Sequence[int]] = None,
    ) -> int:
        if cond is None and doc_ids is None:
            raise ValueError("either cond or doc_ids must be provided")

        table = self._read_table()
        updated = 0

        target_ids: Optional[set[int]] = None
        if doc_ids is not None:
            target_ids = set(int(x) for x in doc_ids)

        for doc in self._iter_docs(table):
            if target_ids is not None:
                if doc.doc_id not in target_ids:
                    continue
            else:
                if cond is not None and not cond(doc):
                    continue

            # Apply update
            new_doc = dict(doc)
            if callable(fields):
                fields(new_doc)
            else:
                if not isinstance(fields, dict):
                    raise TypeError("fields must be a dict or callable")
                new_doc.update(fields)

            table[str(doc.doc_id)] = new_doc
            updated += 1

        if updated:
            self._write_table(table)
        return updated

    def remove(self, cond: Optional[Query] = None, *, doc_ids: Optional[Sequence[int]] = None) -> int:
        if cond is None and doc_ids is None:
            raise ValueError("either cond or doc_ids must be provided")

        table = self._read_table()
        removed = 0

        if doc_ids is not None:
            for did in set(int(x) for x in doc_ids):
                if str(did) in table:
                    del table[str(did)]
                    removed += 1
        else:
            # Remove all matching
            to_delete: List[str] = []
            for doc in self._iter_docs(table):
                if cond is not None and cond(doc):
                    to_delete.append(str(doc.doc_id))
            for k in to_delete:
                if k in table:
                    del table[k]
                    removed += 1

        if removed:
            self._write_table(table)
        return removed

    def truncate(self) -> None:
        self._write_table({})

    # Simple analytics helpers

    def count(self, cond: Query) -> int:
        return len(self.search(cond))

    def sum(self, field: str, cond: Optional[Query] = None, *, default: float = 0.0) -> float:
        total = 0.0
        for doc in self.all() if cond is None else self.search(cond):
            v = doc.get(field, None)
            if isinstance(v, (int, float)):
                total += float(v)
        return total if total != 0.0 else float(default) if not (cond is None and self.all()) else total

    def group_count(self, key: str, cond: Optional[Query] = None) -> Dict[Any, int]:
        out: Dict[Any, int] = {}
        docs = self.all() if cond is None else self.search(cond)
        for d in docs:
            k = d.get(key, None)
            out[k] = out.get(k, 0) + 1
        return out

    def unfinished_per_project(
        self,
        *,
        project_field: str = "project",
        status_field: str = "status",
        done_values: Iterable[Any] = ("done", "completed", "closed"),
    ) -> Dict[Any, int]:
        done_set = set(done_values)
        out: Dict[Any, int] = {}
        for d in self.all():
            status = d.get(status_field, None)
            if status in done_set:
                continue
            proj = d.get(project_field, None)
            out[proj] = out.get(proj, 0) + 1
        return out