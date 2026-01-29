from typing import Any, Callable, Dict, List, Optional, Union
import threading
import copy

class Table:
    def __init__(self, name: str, storage, cache: Optional[Dict]=None):
        self.name = name
        self._storage = storage
        self._lock = threading.RLock()
        self._cache = cache if cache is not None else {}

    def _read(self) -> List[Dict]:
        with self._lock:
            db = self._storage.read()
            tables = db.setdefault('_tables', {})
            table = tables.setdefault(self.name, [])
            return copy.deepcopy(table)

    def _write(self, rows: List[Dict]):
        with self._lock:
            db = self._storage.read()
            tables = db.setdefault('_tables', {})
            tables[self.name] = rows
            self._storage.write(db)

    def all(self) -> List[Dict]:
        return self._read()

    def insert(self, document: Dict[str, Any]) -> int:
        with self._lock:
            table = self._read()
            doc = dict(document)
            doc['id'] = self._next_id(table)
            table.append(doc)
            self._write(table)
            return doc['id']

    def insert_multiple(self, documents: List[Dict[str, Any]]) -> List[int]:
        ids = []
        for doc in documents:
            ids.append(self.insert(doc))
        return ids

    def get(self, cond: Optional[Callable[[Dict], bool]]=None, **kwargs) -> Optional[Dict]:
        for doc in self._read():
            if cond and cond(doc):
                return doc
            if kwargs and all(doc.get(k) == v for k, v in kwargs.items()):
                return doc
        return None

    def search(self, cond: Optional[Callable[[Dict], bool]]=None, **kwargs) -> List[Dict]:
        result = []
        for doc in self._read():
            if cond and cond(doc):
                result.append(doc)
            elif kwargs and all(doc.get(k) == v for k, v in kwargs.items()):
                result.append(doc)
            elif not cond and not kwargs:
                result.append(doc)
        return result

    def update(self, fields: Dict[str, Any], cond: Optional[Callable[[Dict], bool]]=None, **kwargs) -> int:
        updated = 0
        table = self._read()
        for doc in table:
            if cond and cond(doc):
                doc.update(fields)
                updated += 1
            elif kwargs and all(doc.get(k) == v for k, v in kwargs.items()):
                doc.update(fields)
                updated += 1
        if updated:
            self._write(table)
        return updated

    def remove(self, cond: Optional[Callable[[Dict], bool]]=None, **kwargs) -> int:
        table = self._read()
        new_table = []
        removed = 0
        for doc in table:
            if cond and cond(doc):
                removed += 1
            elif kwargs and all(doc.get(k) == v for k, v in kwargs.items()):
                removed += 1
            else:
                new_table.append(doc)
        if removed:
            self._write(new_table)
        return removed

    def count(self, cond: Optional[Callable[[Dict], bool]]=None, **kwargs) -> int:
        return len(self.search(cond, **kwargs))

    def _next_id(self, table: List[Dict]) -> int:
        if not table:
            return 1
        return max(doc.get('id', 0) for doc in table) + 1