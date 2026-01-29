"""
Light-weight Table abstraction compatible with a subset of dataset.Table.
"""
from __future__ import annotations

import sqlite3
from typing import List, Dict, Iterator, Any, Sequence, Union

COLTYPE_DEFAULT = "TEXT"


class Table:
    def __init__(self, db, name: str):
        self._db = db  # instance of Database
        self.name = name
        self._columns: List[str] = []  # cached column list
        self._ensure_exists()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _ensure_exists(self) -> None:
        """
        Create the physical table if it does not yet exist.  A generic ID
        column is added to mirror behaviour of the reference library.
        """
        sql = f"""
            CREATE TABLE IF NOT EXISTS "{self.name}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT
            )
        """
        self._db.connection.execute(sql)
        self._refresh_columns()

    def _refresh_columns(self) -> None:
        cur = self._db.connection.execute(f'PRAGMA table_info("{self.name}")')
        self._columns = [row["name"] for row in cur.fetchall()]

    def _ensure_columns(self, cols: Sequence[str]) -> None:
        """
        Add any of *cols* that are not present in the table.
        """
        missing = [c for c in cols if c not in self._columns]
        for col in missing:
            self._db.connection.execute(
                f'ALTER TABLE "{self.name}" ADD COLUMN "{col}" {COLTYPE_DEFAULT}'
            )
        if missing:
            self._refresh_columns()

    # ------------------------------------------------------------------
    # Public attributes and dunder methods
    # ------------------------------------------------------------------
    @property
    def columns(self) -> List[str]:
        self._refresh_columns()
        return list(self._columns)

    def __len__(self) -> int:
        cur = self._db.connection.execute(f'SELECT COUNT(*) FROM "{self.name}"')
        return cur.fetchone()[0]

    # ------------------------------------------------------------------
    # Insert helpers
    # ------------------------------------------------------------------
    def insert(self, row: Dict[str, Any]) -> int:
        if not row:
            raise ValueError("Row must contain at least one column/value.")
        self._ensure_columns(row.keys())
        cols = list(row.keys())
        placeholders = ", ".join([f":{c}" for c in cols])
        colnames = ", ".join([f'"{c}"' for c in cols])
        sql = f'INSERT INTO "{self.name}" ({colnames}) VALUES ({placeholders})'
        cur = self._db.connection.execute(sql, row)
        return cur.lastrowid

    def insert_many(self, rows: List[Dict[str, Any]], chunk_size: int | None = None):
        if not rows:
            return
        # Discover full set of columns across rows
        all_columns = set()
        for r in rows:
            all_columns.update(r.keys())
        self._ensure_columns(all_columns)

        col_list = sorted(all_columns)
        colnames = ", ".join([f'"{c}"' for c in col_list])
        placeholders = ", ".join([f":{c}" for c in col_list])
        sql = f'INSERT INTO "{self.name}" ({colnames}) VALUES ({placeholders})'

        if chunk_size is None or chunk_size <= 0:
            chunk_size = len(rows)

        for i in range(0, len(rows), chunk_size):
            batch = rows[i : i + chunk_size]
            # Ensure every row has all keys (SQLite will insert NULL for missing)
            fixed = [
                {c: row.get(c, None) for c in col_list}
                for row in batch
            ]
            self._db.connection.executemany(sql, fixed)

    # ------------------------------------------------------------------
    # Update / upsert / delete
    # ------------------------------------------------------------------
    def update(self, row: Dict[str, Any], keys: Union[str, Sequence[str]]) -> int:
        if isinstance(keys, str):
            keys = [keys]
        self._ensure_columns(row.keys())
        set_cols = [c for c in row.keys() if c not in keys]
        if not set_cols:
            return 0  # Nothing to update
        set_clause = ", ".join([f'"{c}" = :{c}' for c in set_cols])
        where_clause = " AND ".join([f'"{k}" = :{k}' for k in keys])
        sql = f'UPDATE "{self.name}" SET {set_clause} WHERE {where_clause}'
        cur = self._db.connection.execute(sql, row)
        return cur.rowcount

    def upsert(self, row: Dict[str, Any], keys: Union[str, Sequence[str]]) -> None:
        updated = self.update(row, keys)
        if updated == 0:
            self.insert(row)

    def delete(self, **filters) -> int:
        if filters:
            where_clause = " AND ".join([f'"{k}" = :{k}' for k in filters])
            sql = f'DELETE FROM "{self.name}" WHERE {where_clause}'
            cur = self._db.connection.execute(sql, filters)
        else:
            sql = f'DELETE FROM "{self.name}"'
            cur = self._db.connection.execute(sql)
        return cur.rowcount

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    def _select(
        self, where: str | None = None, params: Dict[str, Any] | None = None
    ) -> Iterator[Dict[str, Any]]:
        sql = f'SELECT * FROM "{self.name}"'
        if where:
            sql += f" WHERE {where}"
        cur = self._db.connection.execute(sql, params or {})
        columns = [d[0] for d in cur.description]
        for row in cur:
            yield {col: row[idx] for idx, col in enumerate(columns)}

    def all(self) -> List[Dict[str, Any]]:
        return list(self._select())

    def find(self, **filters) -> Iterator[Dict[str, Any]]:
        if filters:
            where_clause = " AND ".join([f'"{k}" = :{k}' for k in filters])
            return self._select(where_clause, filters)
        else:
            return self._select()

    def find_one(self, **filters) -> Dict[str, Any] | None:
        if filters:
            where_clause = " AND ".join([f'"{k}" = :{k}' for k in filters])
            sql = f'SELECT * FROM "{self.name}" WHERE {where_clause} LIMIT 1'
            cur = self._db.connection.execute(sql, filters)
        else:
            sql = f'SELECT * FROM "{self.name}" LIMIT 1'
            cur = self._db.connection.execute(sql)
        row = cur.fetchone()
        if row is None:
            return None
        columns = [d[0] for d in cur.description]
        return {col: row[idx] for idx, col in enumerate(columns)}

    def distinct(self, column: str) -> List[Any]:
        sql = f'SELECT DISTINCT "{column}" FROM "{self.name}"'
        cur = self._db.connection.execute(sql)
        return [row[0] for row in cur.fetchall()]

    def count(self, **filters) -> int:
        if filters:
            where_clause = " AND ".join([f'"{k}" = :{k}' for k in filters])
            sql = f'SELECT COUNT(*) FROM "{self.name}" WHERE {where_clause}'
            cur = self._db.connection.execute(sql, filters)
        else:
            sql = f'SELECT COUNT(*) FROM "{self.name}"'
            cur = self._db.connection.execute(sql)
        return cur.fetchone()[0]

    # ------------------------------------------------------------------
    # Index helpers
    # ------------------------------------------------------------------
    def _index_name(self, columns: Sequence[str]) -> str:
        colpart = "_".join(columns)
        return f"idx_{self.name}_{colpart}"

    def create_index(self, columns: Union[str, Sequence[str]]):
        if isinstance(columns, str):
            columns = [columns]
        index_name = self._index_name(columns)
        collist = ", ".join([f'"{c}"' for c in columns])
        sql = f'CREATE INDEX IF NOT EXISTS "{index_name}" ON "{self.name}" ({collist})'
        self._db.connection.execute(sql)

    def has_index(self, columns: Union[str, Sequence[str]]) -> bool:
        if isinstance(columns, str):
            columns = [columns]
        index_name = self._index_name(columns)
        sql = """
            SELECT name FROM sqlite_master
            WHERE type='index' AND name=:name
        """
        cur = self._db.connection.execute(sql, {"name": index_name})
        return cur.fetchone() is not None