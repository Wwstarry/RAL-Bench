from __future__ import annotations

import copy
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Union

from .queries import QueryInstance


class Table:
    def __init__(self, db: Any, name: str):
        self._db = db
        self.name = name

    def _read_table(self) -> Dict[str, Any]:
        data = self._db._read()
        tbl = self._db._get_table_data(data, self.name)
        return data, tbl

    def _iter_docs(self, table_data: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
        for _, doc in table_data.items():
            if isinstance(doc, dict):
                yield doc

    def _next_id(self, table_data: Dict[str, Any]) -> int:
        max_id = 0
        for k, doc in table_data.items():
            try:
                if isinstance(doc, dict) and "_id" in doc:
                    max_id = max(max_id, int(doc["_id"]))
                else:
                    max_id = max(max_id, int(k))
            except Exception:
                continue
        return max_id + 1

    def insert(self, document: Dict[str, Any]) -> int:
        with self._db._lock:
            data, tbl = self._read_table()
            doc_id = self._next_id(tbl)
            doc = copy.deepcopy(document)
            doc["_id"] = doc_id
            tbl[str(doc_id)] = doc
            self._db._write(data)
            return doc_id

    def insert_multiple(self, documents: List[Dict[str, Any]]) -> List[int]:
        with self._db._lock:
            data, tbl = self._read_table()
            ids: List[int] = []
            for d in documents:
                doc_id = self._next_id(tbl)
                doc = copy.deepcopy(d)
                doc["_id"] = doc_id
                tbl[str(doc_id)] = doc
                ids.append(doc_id)
            self._db._write(data)
            return ids

    def get(self, doc_id: Optional[int] = None, *, query: Optional[QueryInstance] = None) -> Optional[Dict[str, Any]]:
        if doc_id is not None and query is not None:
            raise ValueError("Provide either doc_id or query, not both")
        with self._db._lock:
            data = self._db._read()
            tbl = self._db._get_table_data(data, self.name)
            if doc_id is not None:
                doc = tbl.get(str(doc_id))
                return copy.deepcopy(doc) if isinstance(doc, dict) else None
            if query is not None:
                for doc in self._iter_docs(tbl):
                    if query(doc):
                        return copy.deepcopy(doc)
            return None

    def all(self) -> List[Dict[str, Any]]:
        with self._db._lock:
            data = self._db._read()
            tbl = self._db._get_table_data(data, self.name)
            return [copy.deepcopy(doc) for doc in self._iter_docs(tbl)]

    def search(self, query: QueryInstance) -> List[Dict[str, Any]]:
        with self._db._lock:
            data = self._db._read()
            tbl = self._db._get_table_data(data, self.name)
            return [copy.deepcopy(doc) for doc in self._iter_docs(tbl) if query(doc)]

    def contains(self, query: QueryInstance) -> bool:
        with self._db._lock:
            data = self._db._read()
            tbl = self._db._get_table_data(data, self.name)
            for doc in self._iter_docs(tbl):
                if query(doc):
                    return True
            return False

    def count(self, query: Optional[QueryInstance] = None) -> int:
        with self._db._lock:
            data = self._db._read()
            tbl = self._db._get_table_data(data, self.name)
            if query is None:
                return sum(1 for _ in self._iter_docs(tbl))
            return sum(1 for doc in self._iter_docs(tbl) if query(doc))

    def update(
        self,
        fields: Optional[Dict[str, Any]] = None,
        *,
        doc_ids: Optional[List[int]] = None,
        query: Optional[QueryInstance] = None,
        transform: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None,
    ) -> int:
        if doc_ids is not None and query is not None:
            raise ValueError("Provide either doc_ids or query, not both")
        if doc_ids is None and query is None:
            raise ValueError("update requires doc_ids or query")
        if fields is None and transform is None:
            return 0

        with self._db._lock:
            data, tbl = self._read_table()
            changed = 0

            id_set = set(doc_ids) if doc_ids is not None else None

            for key, doc in list(tbl.items()):
                if not isinstance(doc, dict):
                    continue
                cur_id = doc.get("_id")
                if id_set is not None:
                    if cur_id not in id_set:
                        continue
                elif query is not None:
                    if not query(doc):
                        continue

                new_doc = doc
                if fields is not None:
                    new_doc = dict(new_doc)
                    new_doc.update(fields)
                if transform is not None:
                    new_doc = transform(copy.deepcopy(new_doc))
                    if not isinstance(new_doc, dict):
                        raise ValueError("transform must return a dict document")
                # Preserve id
                new_doc["_id"] = doc.get("_id")
                tbl[str(new_doc["_id"])] = new_doc
                changed += 1

            if changed:
                self._db._write(data)
            return changed

    def remove(
        self,
        doc_ids: Optional[List[int]] = None,
        *,
        query: Optional[QueryInstance] = None,
    ) -> int:
        if doc_ids is not None and query is not None:
            raise ValueError("Provide either doc_ids or query, not both")
        if doc_ids is None and query is None:
            raise ValueError("remove requires doc_ids or query")

        with self._db._lock:
            data, tbl = self._read_table()
            removed = 0
            if doc_ids is not None:
                for did in doc_ids:
                    if str(did) in tbl:
                        del tbl[str(did)]
                        removed += 1
            else:
                to_del: List[str] = []
                for k, doc in tbl.items():
                    if isinstance(doc, dict) and query is not None and query(doc):
                        to_del.append(k)
                for k in to_del:
                    del tbl[k]
                    removed += 1

            if removed:
                self._db._write(data)
            return removed

    def upsert(self, document: Dict[str, Any], *, query: QueryInstance) -> int:
        with self._db._lock:
            data, tbl = self._read_table()
            for k, doc in tbl.items():
                if isinstance(doc, dict) and query(doc):
                    did = int(doc.get("_id"))
                    new_doc = dict(doc)
                    new_doc.update(copy.deepcopy(document))
                    new_doc["_id"] = did
                    tbl[str(did)] = new_doc
                    self._db._write(data)
                    return did
            # insert
            did = self._next_id(tbl)
            doc = copy.deepcopy(document)
            doc["_id"] = did
            tbl[str(did)] = doc
            self._db._write(data)
            return did

    def purge(self) -> None:
        with self._db._lock:
            data = self._db._read()
            data[self.name] = {}
            self._db._write(data)

    # Task-manager helpers
    def create_task(
        self,
        *,
        title: str,
        project: Optional[str] = None,
        status: str = "todo",
        estimate: Optional[float] = None,
        **extra: Any,
    ) -> int:
        doc: Dict[str, Any] = {"title": title, "status": status}
        if project is not None:
            doc["project"] = project
        if estimate is not None:
            doc["estimate"] = estimate
        doc.update(extra)
        return self.insert(doc)

    def unfinished_per_project(self, *, done_statuses: Sequence[str] = ("done", "closed")) -> Dict[str, int]:
        done_set = set(done_statuses)
        counts: Dict[str, int] = {}
        for doc in self.all():
            status = doc.get("status")
            if status in done_set:
                continue
            project = doc.get("project")
            key = project if isinstance(project, str) and project != "" else "(none)"
            counts[key] = counts.get(key, 0) + 1
        return counts