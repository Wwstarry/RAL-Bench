"""
Table implementation: A table is just a list of JSON serialisable documents.

Public API mirrors a subset of TinyDB:

    * insert(doc) -> doc_id
    * all()
    * get(cond)      -> document | None
    * search(cond)   -> list[document]
    * update(fields | callable, cond) -> int (updated)
    * remove(cond)   -> int (removed)
    * count(cond=None) -> int
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from .queries import Condition


class Table:
    """
    Light weight table abstraction.  Operations are committed instantly to the
    owning TinyDB instance so data is persisted to disk.
    """

    def __init__(self, db: "TinyDB", name: str):
        self._db = db
        self._name = name
        self._ensure_structure()

    # ----------------------------------- #
    # Internal helpers
    # ----------------------------------- #
    @property
    def _dataset(self) -> Dict[str, Any]:
        return self._db._data.setdefault(self._name, {"_last_id": 0, "rows": []})

    @property
    def _rows(self) -> List[Dict[str, Any]]:
        return self._dataset["rows"]

    # ----------------------------------- #
    # CRUD
    # ----------------------------------- #
    def insert(self, document: Dict[str, Any]) -> int:
        """
        Insert *document*.  A unique integer *id* will be generated and stored
        in the '_id' field.  Returns the id.
        """
        # Make a shallow copy so passing dict from outside does not keep
        # reference once commit is done.
        doc = dict(document)
        doc_id = self._dataset["_last_id"] + 1
        self._dataset["_last_id"] = doc_id
        doc["_id"] = doc_id
        self._rows.append(doc)
        self._db._flush()
        return doc_id

    def all(self) -> List[Dict[str, Any]]:
        return [dict(row) for row in self._rows]

    def _ensure_structure(self) -> None:
        self._db._data.setdefault(self._name, {"_last_id": 0, "rows": []})

    # ----------------------------------- #
    # Query helpers
    # ----------------------------------- #
    def _as_condition(self, cond) -> Condition:
        if cond is None:
            return Condition(lambda _: True)
        if isinstance(cond, Condition):
            return cond
        if callable(cond):
            return Condition(cond)
        raise TypeError("cond must be a Condition or callable")

    # ----------------------------------- #
    # Higher level operations
    # ----------------------------------- #
    def search(self, cond) -> List[Dict[str, Any]]:
        test = self._as_condition(cond)
        return [dict(row) for row in self._rows if test(row)]

    def get(self, cond) -> Optional[Dict[str, Any]]:
        test = self._as_condition(cond)
        for row in self._rows:
            if test(row):
                return dict(row)
        return None

    def count(self, cond=None) -> int:
        return len(self.search(cond))

    def remove(self, cond) -> int:
        test = self._as_condition(cond)
        to_remove = [row for row in self._rows if test(row)]
        removed = len(to_remove)
        if not removed:
            return 0
        self._dataset["rows"] = [row for row in self._rows if not test(row)]
        self._db._flush()
        return removed

    def update(self, fields_or_func, cond) -> int:
        """
        *fields_or_func* can either be a dictionary of fields to merge into each
        matching document or a callable that mutates and/or returns the new
        document.

        Returns number of updated rows.
        """
        test = self._as_condition(cond)
        updated = 0
        for idx, row in enumerate(list(self._rows)):
            if test(row):
                if callable(fields_or_func):
                    new_row = fields_or_func(dict(row))
                    if new_row is None:
                        # assume in-place modification
                        new_row = row
                else:
                    changes = dict(fields_or_func)
                    new_row = dict(row)
                    new_row.update(changes)
                # Preserve _id
                new_row["_id"] = row["_id"]
                self._rows[idx] = new_row
                updated += 1
        if updated:
            self._db._flush()
        return updated

    # ------------------------------------------------------------------ #
    # Convenience analytics helpers
    # ------------------------------------------------------------------ #
    def unfinished_per(self, field: str = "project") -> Dict[Any, int]:
        """
        Return {value: number_of_unfinished_tasks} grouping by *field*.

        Unfinished = document['status'] not in ('done', 'completed').
        """
        result: Dict[Any, int] = {}
        for row in self._rows:
            status = row.get("status")
            if status in ("done", "completed"):
                continue
            key = row.get(field)
            if key is None:
                key = "<undefined>"
            result[key] = result.get(key, 0) + 1
        return result