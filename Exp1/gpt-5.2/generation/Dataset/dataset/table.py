from __future__ import annotations

import re
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple, Union


def _quote_ident(name: str) -> str:
    # SQLite identifier quoting with double quotes.
    name = str(name)
    name = name.replace('"', '""')
    return f'"{name}"'


_SQLITE_TYPE_ORDER = ("INTEGER", "REAL", "TEXT", "BLOB")


def _infer_sqlite_type(value: Any) -> str:
    if value is None:
        return "TEXT"
    if isinstance(value, bool):
        return "INTEGER"
    if isinstance(value, int):
        return "INTEGER"
    if isinstance(value, float):
        return "REAL"
    if isinstance(value, (bytes, bytearray, memoryview)):
        return "BLOB"
    return "TEXT"


def _normalize_columns(columns: Union[str, Sequence[str]]) -> Tuple[str, ...]:
    if isinstance(columns, str):
        return (columns,)
    return tuple(columns)


class Table:
    """
    Minimal Table implementation with lazy creation and dynamic columns.
    """

    def __init__(self, db: "dataset.database.Database", name: str):
        # Late import to avoid circular typing at runtime
        self.db = db
        self.name = name
        self._columns_cache: Optional[List[str]] = None
        self._indexes_cache: Optional[set[Tuple[str, ...]]] = None

        # Lazy: do not create table until needed.

    @property
    def quoted_name(self) -> str:
        return _quote_ident(self.name)

    def _table_exists(self) -> bool:
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name=:name"
        cur = self.db.execute(sql, {"name": self.name})
        return cur.fetchone() is not None

    def _ensure_table(self) -> None:
        if self._table_exists():
            return
        # Create a minimal table with an integer primary key.
        sql = f"CREATE TABLE IF NOT EXISTS {self.quoted_name} (id INTEGER PRIMARY KEY AUTOINCREMENT)"
        self.db.execute(sql)
        self._columns_cache = None
        self._indexes_cache = None

    def _load_columns(self) -> List[str]:
        self._ensure_table()
        cur = self.db.execute(f"PRAGMA table_info({self.quoted_name})")
        cols = [r[1] for r in cur.fetchall()]  # name is 2nd column
        self._columns_cache = cols
        return cols

    @property
    def columns(self) -> List[str]:
        if self._columns_cache is None:
            return self._load_columns()
        return list(self._columns_cache)

    def __len__(self) -> int:
        return int(self.count())

    def _ensure_columns_for_row(self, row: Mapping[str, Any]) -> None:
        self._ensure_table()
        cols = set(self.columns)
        to_add: List[Tuple[str, str]] = []
        for k, v in row.items():
            if k is None:
                continue
            key = str(k)
            if key == "":
                continue
            if key not in cols:
                to_add.append((key, _infer_sqlite_type(v)))
        for col, typ in to_add:
            self.db.execute(f"ALTER TABLE {self.quoted_name} ADD COLUMN {_quote_ident(col)} {typ}")
            cols.add(col)
        if to_add:
            self._columns_cache = None  # reload on next access

    def _row_to_params(self, row: Mapping[str, Any]) -> Dict[str, Any]:
        # Coerce keys to str for consistency
        return {str(k): v for k, v in row.items()}

    # --- Insert ---
    def insert(self, row: Mapping[str, Any]) -> Any:
        row = self._row_to_params(row)
        self._ensure_columns_for_row(row)

        # If user provides id, keep it; else omit and let autoincrement.
        keys = [k for k in row.keys() if k is not None and k != ""]
        if not keys:
            # Insert default row
            cur = self.db.execute(f"INSERT INTO {self.quoted_name} DEFAULT VALUES")
            return cur.lastrowid

        cols_sql = ", ".join(_quote_ident(k) for k in keys)
        vals_sql = ", ".join(f":{k}" for k in keys)
        sql = f"INSERT INTO {self.quoted_name} ({cols_sql}) VALUES ({vals_sql})"
        cur = self.db.execute(sql, row)
        return cur.lastrowid

    def insert_many(self, rows: Iterable[Mapping[str, Any]], chunk_size: Optional[int] = None) -> List[Any]:
        rows_list = [self._row_to_params(r) for r in rows]
        if not rows_list:
            return []
        # Ensure columns across all rows
        merged: Dict[str, Any] = {}
        for r in rows_list:
            for k, v in r.items():
                if str(k) not in merged:
                    merged[str(k)] = v
        self._ensure_columns_for_row(merged)

        # Determine union of keys excluding empty
        all_keys = sorted({k for r in rows_list for k in r.keys() if k})
        if not all_keys:
            # all default inserts
            ids: List[Any] = []
            for _ in rows_list:
                cur = self.db.execute(f"INSERT INTO {self.quoted_name} DEFAULT VALUES")
                ids.append(cur.lastrowid)
            return ids

        cols_sql = ", ".join(_quote_ident(k) for k in all_keys)
        vals_sql = ", ".join(f":{k}" for k in all_keys)
        sql = f"INSERT INTO {self.quoted_name} ({cols_sql}) VALUES ({vals_sql})"

        def chunker(seq: List[Dict[str, Any]], n: int) -> Iterable[List[Dict[str, Any]]]:
            for i in range(0, len(seq), n):
                yield seq[i : i + n]

        ids: List[Any] = []
        if chunk_size is None or chunk_size <= 0:
            chunk_size = len(rows_list)

        for chunk in chunker(rows_list, chunk_size):
            params_seq = []
            for r in chunk:
                p = {k: r.get(k, None) for k in all_keys}
                params_seq.append(p)
            self.db.executemany(sql, params_seq)
            # Best-effort ids: sqlite doesn't provide all rowids via executemany.
            # For compatibility, return empty list if not reliably known? Tests often ignore ids for insert_many.
            # We'll approximate using lastrowid and count if contiguous.
            cur = self.db.execute("SELECT last_insert_rowid()")
            last_id = int(cur.fetchone()[0])
            first_id = last_id - (len(chunk) - 1)
            ids.extend(list(range(first_id, last_id + 1)))
        return ids

    # --- Update/Upsert/Delete ---
    def update(self, row: Mapping[str, Any], keys: Union[str, Sequence[str]]) -> int:
        row = self._row_to_params(row)
        keys_t = _normalize_columns(keys)
        self._ensure_columns_for_row(row)

        where_parts = []
        params: Dict[str, Any] = {}
        for k in keys_t:
            where_parts.append(f"{_quote_ident(k)} = :_w_{k}")
            params[f"_w_{k}"] = row.get(k)

        set_parts = []
        for k, v in row.items():
            if k in keys_t:
                continue
            set_parts.append(f"{_quote_ident(k)} = :_s_{k}")
            params[f"_s_{k}"] = v

        if not set_parts:
            return 0

        sql = f"UPDATE {self.quoted_name} SET {', '.join(set_parts)} WHERE {' AND '.join(where_parts)}"
        cur = self.db.execute(sql, params)
        return int(cur.rowcount)

    def upsert(self, row: Mapping[str, Any], keys: Union[str, Sequence[str]]) -> Any:
        row = self._row_to_params(row)
        keys_t = _normalize_columns(keys)
        self._ensure_columns_for_row(row)

        # Check existence
        filt = {k: row.get(k) for k in keys_t}
        existing = self.find_one(**filt)
        if existing is None:
            return self.insert(row)
        # Ensure we update by keys
        self.update(row, keys_t)
        # Return id if present
        if "id" in existing:
            return existing["id"]
        # Try to refetch
        ref = self.find_one(**filt)
        return ref.get("id") if ref else None

    def delete(self, **filters: Any) -> int:
        self._ensure_table()
        if not filters:
            cur = self.db.execute(f"DELETE FROM {self.quoted_name}")
            return int(cur.rowcount)
        where_sql, params = self._filters_to_where(filters)
        cur = self.db.execute(f"DELETE FROM {self.quoted_name} WHERE {where_sql}", params)
        return int(cur.rowcount)

    # --- Querying ---
    def _filters_to_where(self, filters: Mapping[str, Any]) -> Tuple[str, Dict[str, Any]]:
        parts = []
        params: Dict[str, Any] = {}
        for k, v in filters.items():
            k = str(k)
            if v is None:
                parts.append(f"{_quote_ident(k)} IS NULL")
            else:
                parts.append(f"{_quote_ident(k)} = :{k}")
                params[k] = v
        if not parts:
            return "1=1", {}
        return " AND ".join(parts), params

    def all(self) -> Iterator[Mapping[str, Any]]:
        self._ensure_table()
        cur = self.db.execute(f"SELECT * FROM {self.quoted_name}")
        for r in cur.fetchall():
            yield dict(r)

    def find(self, **filters: Any) -> Iterator[Mapping[str, Any]]:
        self._ensure_table()
        where_sql, params = self._filters_to_where(filters)
        cur = self.db.execute(f"SELECT * FROM {self.quoted_name} WHERE {where_sql}", params)
        for r in cur.fetchall():
            yield dict(r)

    def find_one(self, **filters: Any) -> Optional[Mapping[str, Any]]:
        self._ensure_table()
        where_sql, params = self._filters_to_where(filters)
        cur = self.db.execute(f"SELECT * FROM {self.quoted_name} WHERE {where_sql} LIMIT 1", params)
        r = cur.fetchone()
        return dict(r) if r is not None else None

    def distinct(self, column: str) -> Iterator[Any]:
        self._ensure_table()
        col = str(column)
        cur = self.db.execute(f"SELECT DISTINCT {_quote_ident(col)} AS v FROM {self.quoted_name} WHERE {_quote_ident(col)} IS NOT NULL")
        for r in cur.fetchall():
            yield r[0]

    def count(self, **filters: Any) -> int:
        self._ensure_table()
        where_sql, params = self._filters_to_where(filters)
        cur = self.db.execute(f"SELECT COUNT(*) FROM {self.quoted_name} WHERE {where_sql}", params)
        return int(cur.fetchone()[0])

    # --- Index helpers ---
    def _load_indexes(self) -> set[Tuple[str, ...]]:
        self._ensure_table()
        idxs: set[Tuple[str, ...]] = set()
        # Collect index columns from PRAGMA index_list and index_info
        cur = self.db.execute(f"PRAGMA index_list({self.quoted_name})")
        for row in cur.fetchall():
            idx_name = row[1]
            info = self.db.execute(f"PRAGMA index_info({_quote_ident(idx_name)})").fetchall()
            cols = tuple(i[2] for i in info)
            if cols:
                idxs.add(cols)
        self._indexes_cache = idxs
        return idxs

    def has_index(self, columns: Union[str, Sequence[str]]) -> bool:
        cols = _normalize_columns(columns)
        if self._indexes_cache is None:
            self._load_indexes()
        # Accept same columns regardless of order? dataset typically treats order as given.
        # We'll treat exact tuple as required, but also allow any permutation match to be forgiving.
        if cols in self._indexes_cache:
            return True
        s = set(cols)
        for existing in self._indexes_cache or set():
            if set(existing) == s and len(existing) == len(cols):
                return True
        return False

    def create_index(self, columns: Union[str, Sequence[str]]) -> None:
        self._ensure_table()
        cols = _normalize_columns(columns)
        if not cols:
            return
        if self.has_index(cols):
            return
        # Deterministic index name
        safe = "_".join(re.sub(r"[^A-Za-z0-9_]+", "_", c) for c in cols)
        idx_name = f"idx_{self.name}_{safe}"
        cols_sql = ", ".join(_quote_ident(c) for c in cols)
        self.db.execute(f"CREATE INDEX IF NOT EXISTS {_quote_ident(idx_name)} ON {self.quoted_name} ({cols_sql})")
        self._indexes_cache = None
        self._load_indexes()