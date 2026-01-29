from __future__ import annotations

import copy
import time
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

from .queries import Query


Document = Dict[str, Any]
DocID = int


class Table:
    def __init__(self, db: "Database", name: str):
        self._db = db
        self.name = name

    # ---------- internal helpers ----------
    def _ensure_table(self, data: Dict[str, Any]) -> Dict[str, Any]:
        tables = data.setdefault("tables", {})
        t = tables.get(self.name)
        if t is None:
            t = {"_last_id": 0, "docs": {}}
            tables[self.name] = t
        t.setdefault("_last_id", 0)
        t.setdefault("docs", {})
        if not isinstance(t["docs"], dict):
            raise ValueError(f"Corrupt table {self.name}: docs is not a dict")
        return t

    def _now(self) -> float:
        return time.time()

    def _next_id(self, table_obj: Dict[str, Any]) -> int:
        table_obj["_last_id"] = int(table_obj.get("_last_id", 0)) + 1
        return int(table_obj["_last_id"])

    def _normalize_doc(self, doc: Document) -> Document:
        if not isinstance(doc, dict):
            raise TypeError("Document must be a dict")
        return copy.deepcopy(doc)

    def _iter_docs(self, data: Dict[str, Any]) -> Iterable[Tuple[int, Document]]:
        t = self._ensure_table(data)
        for k, v in t["docs"].items():
            try:
                doc_id = int(k)
            except Exception:
                continue
            if isinstance(v, dict):
                yield doc_id, v

    def _get_doc(self, data: Dict[str, Any], doc_id: int) -> Optional[Document]:
        t = self._ensure_table(data)
        raw = t["docs"].get(str(int(doc_id)))
        if isinstance(raw, dict):
            return raw
        return None

    # ---------- CRUD ----------
    def insert(self, doc: Document) -> int:
        with self._db._lock:
            data = self._db._storage.read()
            t = self._ensure_table(data)
            new_id = self._next_id(t)
            d = self._normalize_doc(doc)
            d["id"] = new_id
            d.setdefault("created_at", self._now())
            d.setdefault("updated_at", d["created_at"])
            t["docs"][str(new_id)] = d
            self._db._storage.write(data)
            return new_id

    def insert_many(self, docs: Iterable[Document]) -> List[int]:
        ids: List[int] = []
        with self._db._lock:
            data = self._db._storage.read()
            t = self._ensure_table(data)
            for doc in docs:
                new_id = self._next_id(t)
                d = self._normalize_doc(doc)
                d["id"] = new_id
                d.setdefault("created_at", self._now())
                d.setdefault("updated_at", d["created_at"])
                t["docs"][str(new_id)] = d
                ids.append(new_id)
            self._db._storage.write(data)
        return ids

    def get(self, doc_id: int) -> Optional[Document]:
        with self._db._lock:
            data = self._db._storage.read()
            d = self._get_doc(data, doc_id)
            return copy.deepcopy(d) if d is not None else None

    def all(self) -> List[Document]:
        with self._db._lock:
            data = self._db._storage.read()
            docs = [copy.deepcopy(v) | {"id": int(k)} for k, v in self._ensure_table(data)["docs"].items() if isinstance(v, dict)]
            docs.sort(key=lambda x: int(x.get("id", 0)))
            return docs

    def search(self, query: Optional[Query] = None, *, sort: Optional[Union[str, Callable[[Document], Any]]] = None, reverse: bool = False, limit: Optional[int] = None) -> List[Document]:
        with self._db._lock:
            data = self._db._storage.read()
            out: List[Document] = []
            for doc_id, raw in self._iter_docs(data):
                d = dict(raw)
                d["id"] = doc_id
                if query is None or query(d):
                    out.append(copy.deepcopy(d))
            if sort is not None:
                if isinstance(sort, str):
                    keyfn = lambda d, f=sort: d.get(f)
                else:
                    keyfn = sort
                out.sort(key=keyfn, reverse=reverse)
            if limit is not None:
                out = out[: int(limit)]
            return out

    def count(self, query: Optional[Query] = None) -> int:
        return len(self.search(query))

    def update(self, fields: Dict[str, Any], query: Optional[Query] = None, *, doc_ids: Optional[Iterable[int]] = None) -> int:
        if query is None and doc_ids is None:
            raise ValueError("Provide query and/or doc_ids to update")
        if not isinstance(fields, dict):
            raise TypeError("fields must be a dict")

        updated = 0
        with self._db._lock:
            data = self._db._storage.read()
            t = self._ensure_table(data)

            targets: List[int] = []
            if doc_ids is not None:
                targets.extend(int(x) for x in doc_ids)

            if query is not None:
                for doc_id, raw in self._iter_docs(data):
                    d = dict(raw)
                    d["id"] = doc_id
                    if query(d):
                        targets.append(doc_id)

            seen = set()
            for doc_id in targets:
                if doc_id in seen:
                    continue
                seen.add(doc_id)
                raw = t["docs"].get(str(doc_id))
                if not isinstance(raw, dict):
                    continue
                raw.update(copy.deepcopy(fields))
                raw["updated_at"] = self._now()
                t["docs"][str(doc_id)] = raw
                updated += 1

            if updated:
                self._db._storage.write(data)
        return updated

    def upsert(self, doc: Document, query: Query) -> List[int]:
        matches = self.search(query)
        if not matches:
            return [self.insert(doc)]
        ids = [m["id"] for m in matches]
        self.update(doc, doc_ids=ids)
        return ids

    def remove(self, query: Optional[Query] = None, *, doc_ids: Optional[Iterable[int]] = None) -> int:
        if query is None and doc_ids is None:
            raise ValueError("Provide query and/or doc_ids to remove")
        removed = 0
        with self._db._lock:
            data = self._db._storage.read()
            t = self._ensure_table(data)

            targets: List[int] = []
            if doc_ids is not None:
                targets.extend(int(x) for x in doc_ids)

            if query is not None:
                for doc_id, raw in self._iter_docs(data):
                    d = dict(raw)
                    d["id"] = doc_id
                    if query(d):
                        targets.append(doc_id)

            seen = set()
            for doc_id in targets:
                if doc_id in seen:
                    continue
                seen.add(doc_id)
                if str(doc_id) in t["docs"]:
                    del t["docs"][str(doc_id)]
                    removed += 1

            if removed:
                self._db._storage.write(data)
        return removed

    def truncate(self) -> None:
        with self._db._lock:
            data = self._db._storage.read()
            tables = data.setdefault("tables", {})
            tables[self.name] = {"_last_id": 0, "docs": {}}
            self._db._storage.write(data)

    # ---------- task-manager convenience ----------
    def create_task(
        self,
        title: str,
        *,
        project: str = "inbox",
        status: str = "todo",
        estimate: Optional[float] = None,
        due: Optional[Any] = None,
        tags: Optional[List[str]] = None,
        description: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> int:
        doc: Document = {
            "type": "task",
            "title": title,
            "project": project,
            "status": status,
        }
        if estimate is not None:
            doc["estimate"] = estimate
        if due is not None:
            doc["due"] = due
        if tags is not None:
            doc["tags"] = list(tags)
        if description is not None:
            doc["description"] = description
        if extra:
            doc.update(copy.deepcopy(extra))
        return self.insert(doc)

    def set_status(self, doc_id: int, status: str) -> bool:
        return self.update({"status": status}, doc_ids=[doc_id]) == 1

    def set_estimate(self, doc_id: int, estimate: Optional[float]) -> bool:
        fields: Dict[str, Any] = {"estimate": estimate}
        return self.update(fields, doc_ids=[doc_id]) == 1

    def move_to_project(self, doc_id: int, project: str) -> bool:
        return self.update({"project": project}, doc_ids=[doc_id]) == 1