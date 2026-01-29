import copy
from typing import Any, Callable, Dict, Iterable, List, Optional, Union

from .queries import Query


UpdateArg = Union[Dict[str, Any], Callable[[Dict[str, Any]], Optional[Dict[str, Any]]]]
QueryArg = Union[Query, Callable[[Dict[str, Any]], bool], Dict[str, Any]]


class Table:
    def __init__(self, database: "Database", name: str) -> None:
        self._db = database
        self.name = name
        # Ensure backing store exists
        self._ensure_store()

    def _ensure_store(self) -> None:
        root = self._db._data
        if "tables" not in root:
            root["tables"] = {}
        if self.name not in root["tables"]:
            root["tables"][self.name] = {"docs": [], "next_id": 1}
            self._db._save()

    @property
    def _store(self) -> Dict[str, Any]:
        return self._db._data["tables"][self.name]

    @property
    def _docs(self) -> List[Dict[str, Any]]:
        return self._store["docs"]

    def _next_id(self) -> int:
        nid = int(self._store.get("next_id", 1))
        self._store["next_id"] = nid + 1
        return nid

    def _find_index_by_id(self, doc_id: int) -> Optional[int]:
        for i, d in enumerate(self._docs):
            if d.get("id") == doc_id:
                return i
        return None

    def insert(self, doc: Dict[str, Any]) -> int:
        if not isinstance(doc, dict):
            raise TypeError("Document must be a dict")
        d = copy.deepcopy(doc)
        if "id" in d:
            if self.contains(doc_id=d["id"]):
                raise ValueError(f"Document with id={d['id']} already exists")
            # Keep provided id but ensure next_id is ahead
            if isinstance(d["id"], int):
                self._store["next_id"] = max(self._store.get("next_id", 1), d["id"] + 1)
        else:
            d["id"] = self._next_id()
        self._docs.append(d)
        self._db._save()
        return d["id"]

    def insert_multiple(self, docs: Iterable[Dict[str, Any]]) -> List[int]:
        ids: List[int] = []
        for doc in docs:
            ids.append(self.insert(doc))
        return ids

    def all(self) -> List[Dict[str, Any]]:
        return copy.deepcopy(self._docs)

    def get(self, query: Optional[QueryArg] = None, doc_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        if doc_id is not None:
            idx = self._find_index_by_id(doc_id)
            return copy.deepcopy(self._docs[idx]) if idx is not None else None
        if query is None:
            return None
        for d in self._docs:
            if self._matches(d, query):
                return copy.deepcopy(d)
        return None

    def search(self, query: Optional[QueryArg]) -> List[Dict[str, Any]]:
        if query is None:
            return self.all()
        out: List[Dict[str, Any]] = []
        for d in self._docs:
            if self._matches(d, query):
                out.append(copy.deepcopy(d))
        return out

    def count(self, query: Optional[QueryArg] = None) -> int:
        if query is None:
            return len(self._docs)
        total = 0
        for d in self._docs:
            if self._matches(d, query):
                total += 1
        return total

    def contains(self, query: Optional[QueryArg] = None, doc_id: Optional[int] = None) -> bool:
        if doc_id is not None:
            return self._find_index_by_id(doc_id) is not None
        if query is None:
            return False
        for d in self._docs:
            if self._matches(d, query):
                return True
        return False

    def update(self, fields: UpdateArg, query: Optional[QueryArg] = None, doc_ids: Optional[Iterable[int]] = None) -> int:
        targets: List[int] = []
        if doc_ids is not None:
            for did in doc_ids:
                idx = self._find_index_by_id(int(did))
                if idx is not None:
                    targets.append(idx)
        else:
            if query is None:
                raise ValueError("update requires a query or doc_ids")
            for i, d in enumerate(self._docs):
                if self._matches(d, query):
                    targets.append(i)

        updated = 0
        for idx in targets:
            doc = self._docs[idx]
            if callable(fields):
                result = fields(copy.deepcopy(doc))
                if result is None:
                    # Assume in-place mutation not supported; ignore
                    pass
                else:
                    if not isinstance(result, dict):
                        raise TypeError("Update callable must return dict or None")
                    # Prevent id overwrite
                    result = {k: v for k, v in result.items() if k != "id"}
                    doc.update(result)
                    updated += 1
            else:
                # dict of fields
                if not isinstance(fields, dict):
                    raise TypeError("fields must be dict or callable")
                # Prevent id overwrite
                to_set = {k: v for k, v in fields.items() if k != "id"}
                doc.update(to_set)
                updated += 1

        if updated:
            self._db._save()
        return updated

    def upsert(self, doc: Dict[str, Any], query: Optional[QueryArg] = None) -> int:
        if not isinstance(doc, dict):
            raise TypeError("Document must be a dict")
        # If id present, update or insert accordingly
        if "id" in doc and isinstance(doc["id"], int):
            idx = self._find_index_by_id(doc["id"])
            if idx is not None:
                # Update existing
                new_doc = copy.deepcopy(doc)
                new_doc_id = self._docs[idx]["id"]
                new_doc["id"] = new_doc_id
                self._docs[idx].update({k: v for k, v in new_doc.items() if k != "id"})
                self._db._save()
                return new_doc_id
            else:
                return self.insert(doc)

        # Else use query if provided
        if query is not None:
            for i, d in enumerate(self._docs):
                if self._matches(d, query):
                    self._docs[i].update({k: v for k, v in doc.items() if k != "id"})
                    self._db._save()
                    return self._docs[i]["id"]

        # Else insert
        return self.insert(doc)

    def remove(self, query: Optional[QueryArg] = None, doc_ids: Optional[Iterable[int]] = None) -> int:
        targets: List[int] = []
        if doc_ids is not None:
            for did in doc_ids:
                idx = self._find_index_by_id(int(did))
                if idx is not None:
                    targets.append(idx)
        else:
            if query is None:
                raise ValueError("remove requires a query or doc_ids")
            for i, d in enumerate(self._docs):
                if self._matches(d, query):
                    targets.append(i)

        # Remove from end to keep indices valid
        targets = sorted(set(targets), reverse=True)
        removed = 0
        for idx in targets:
            del self._docs[idx]
            removed += 1
        if removed:
            self._db._save()
        return removed

    def truncate(self) -> None:
        self._store["docs"] = []
        self._store["next_id"] = 1
        self._db._save()

    def _matches(self, doc: Dict[str, Any], query: QueryArg) -> bool:
        if isinstance(query, dict):
            # equality match on keys
            for k, v in query.items():
                if doc.get(k) != v:
                    return False
            return True
        if isinstance(query, Query):
            return query(doc)
        if callable(query):
            return bool(query(doc))
        raise TypeError("Unsupported query type")