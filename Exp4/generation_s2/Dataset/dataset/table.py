import re
import sqlite3
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple, Union


_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _quote_ident(name: str) -> str:
    # We allow broader table/column names by quoting with double quotes.
    # Escape internal quotes by doubling them.
    return '"' + name.replace('"', '""') + '"'


def _normalize_columns(columns: Union[str, Sequence[str]]) -> Tuple[str, ...]:
    if isinstance(columns, str):
        return (columns,)
    return tuple(columns)


def _infer_sqlite_type(value: Any) -> str:
    # Keep it simple and permissive.
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


class Table:
    """
    A lightweight table wrapper which:
    - creates the table lazily on first access/insert/query operations
    - adds missing columns dynamically on insert/update/upsert
    """

    def __init__(self, db: "dataset.database.Database", name: str):
        self.db = db
        self.name = name
        self._quoted = _quote_ident(name)
        self._known_columns: Optional[List[str]] = None

        # Ensure a meta table for index tracking exists.
        self._ensure_meta()

    def _ensure_meta(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS __dataset_indexes__ (
                table_name TEXT NOT NULL,
                columns TEXT NOT NULL,
                UNIQUE(table_name, columns)
            )
            """
        )

    def _ensure_table(self) -> None:
        # Create table if it doesn't exist.
        self.db.execute(f"CREATE TABLE IF NOT EXISTS {self._quoted} (id INTEGER PRIMARY KEY AUTOINCREMENT)")
        self._refresh_columns()

    def _refresh_columns(self) -> None:
        cur = self.db.execute(f"PRAGMA table_info({self._quoted})")
        cols = [r["name"] for r in cur.fetchall()]
        self._known_columns = cols

    @property
    def columns(self) -> List[str]:
        self._ensure_table()
        if self._known_columns is None:
            self._refresh_columns()
        return list(self._known_columns or [])

    def __len__(self) -> int:
        self._ensure_table()
        cur = self.db.execute(f"SELECT COUNT(*) AS c FROM {self._quoted}")
        return int(cur.fetchone()["c"])

    def _ensure_columns_for_row(self, row: Dict[str, Any]) -> None:
        self._ensure_table()
        if self._known_columns is None:
            self._refresh_columns()
        existing = set(self._known_columns or [])
        for key, val in row.items():
            if key is None:
                continue
            if key in existing:
                continue
            # Avoid creating "id" column if user passes id; table already has id.
            if key == "id":
                continue
            coltype = _infer_sqlite_type(val)
            self.db.execute(f"ALTER TABLE {self._quoted} ADD COLUMN {_quote_ident(key)} {coltype}")
            existing.add(key)
        self._refresh_columns()

    def _where_clause(self, filters: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        if not filters:
            return "", {}
        parts = []
        params: Dict[str, Any] = {}
        for i, (k, v) in enumerate(filters.items()):
            pname = f"w_{i}"
            if v is None:
                parts.append(f"{_quote_ident(k)} IS NULL")
            else:
                parts.append(f"{_quote_ident(k)} = :{pname}")
                params[pname] = v
        return " WHERE " + " AND ".join(parts), params

    def insert(self, row: Dict[str, Any]) -> Any:
        if row is None or not isinstance(row, dict):
            raise TypeError("row must be a dict")
        self._ensure_columns_for_row(row)

        keys = [k for k in row.keys() if k != "id"]
        if not keys:
            cur = self.db.execute(f"INSERT INTO {self._quoted} DEFAULT VALUES")
            return cur.lastrowid

        cols_sql = ", ".join(_quote_ident(k) for k in keys)
        vals_sql = ", ".join(f":{k}" for k in keys)
        params = {k: row.get(k) for k in keys}
        cur = self.db.execute(f"INSERT INTO {self._quoted} ({cols_sql}) VALUES ({vals_sql})", params)
        return cur.lastrowid

    def insert_many(self, rows: Iterable[Dict[str, Any]], chunk_size: Optional[int] = None) -> None:
        if rows is None:
            return
        rows_iter = iter(rows)
        batch: List[Dict[str, Any]] = []

        def flush(b: List[Dict[str, Any]]) -> None:
            if not b:
                return
            # Ensure columns for union of keys in batch.
            union: Dict[str, Any] = {}
            for r in b:
                if isinstance(r, dict):
                    for k, v in r.items():
                        if k not in union:
                            union[k] = v
            self._ensure_columns_for_row(union)

            # Determine stable key list: union of keys excluding id.
            keyset = set()
            for r in b:
                keyset.update([k for k in r.keys() if k != "id"])
            keys = sorted(keyset)

            if not keys:
                # Insert default rows one by one (rare).
                for _ in b:
                    self.db.execute(f"INSERT INTO {self._quoted} DEFAULT VALUES")
                return

            cols_sql = ", ".join(_quote_ident(k) for k in keys)
            vals_sql = ", ".join(f":{k}" for k in keys)
            sql = f"INSERT INTO {self._quoted} ({cols_sql}) VALUES ({vals_sql})"
            params_list = [{k: r.get(k) for k in keys} for r in b]
            self.db.executemany(sql, params_list)

        if chunk_size is None or chunk_size <= 0:
            # consume all at once
            all_rows = [r for r in rows_iter]
            flush(all_rows)
            return

        for r in rows_iter:
            if not isinstance(r, dict):
                raise TypeError("rows must contain dicts")
            batch.append(r)
            if len(batch) >= chunk_size:
                flush(batch)
                batch = []
        flush(batch)

    def all(self) -> Iterator[Dict[str, Any]]:
        self._ensure_table()
        cur = self.db.execute(f"SELECT * FROM {self._quoted}")
        for row in cur.fetchall():
            yield dict(row)

    def find(self, **filters: Any) -> Iterator[Dict[str, Any]]:
        self._ensure_table()
        where_sql, params = self._where_clause(filters)
        cur = self.db.execute(f"SELECT * FROM {self._quoted}{where_sql}", params)
        for row in cur.fetchall():
            yield dict(row)

    def find_one(self, **filters: Any) -> Optional[Dict[str, Any]]:
        self._ensure_table()
        where_sql, params = self._where_clause(filters)
        cur = self.db.execute(f"SELECT * FROM {self._quoted}{where_sql} LIMIT 1", params)
        r = cur.fetchone()
        return dict(r) if r is not None else None

    def distinct(self, column: str) -> List[Any]:
        self._ensure_table()
        cur = self.db.execute(f"SELECT DISTINCT {_quote_ident(column)} AS v FROM {self._quoted}")
        return [r["v"] for r in cur.fetchall()]

    def count(self, **filters: Any) -> int:
        self._ensure_table()
        where_sql, params = self._where_clause(filters)
        cur = self.db.execute(f"SELECT COUNT(*) AS c FROM {self._quoted}{where_sql}", params)
        return int(cur.fetchone()["c"])

    def delete(self, **filters: Any) -> int:
        self._ensure_table()
        where_sql, params = self._where_clause(filters)
        cur = self.db.execute(f"DELETE FROM {self._quoted}{where_sql}", params)
        return int(cur.rowcount if cur.rowcount is not None else 0)

    def update(self, row: Dict[str, Any], keys: Union[str, Sequence[str]]) -> int:
        if row is None or not isinstance(row, dict):
            raise TypeError("row must be a dict")
        key_cols = _normalize_columns(keys)
        if not key_cols:
            raise ValueError("keys must not be empty")

        self._ensure_columns_for_row(row)

        # Build WHERE from keys
        where_filters: Dict[str, Any] = {}
        for k in key_cols:
            if k not in row:
                raise KeyError(f"Missing key column in row: {k}")
            where_filters[k] = row.get(k)

        # SET columns: all except key columns
        set_cols = [k for k in row.keys() if k not in key_cols and k != "id"]
        if not set_cols:
            return 0

        set_sql = ", ".join(f"{_quote_ident(k)} = :s_{k}" for k in set_cols)
        where_sql_parts = []
        params: Dict[str, Any] = {}
        for k in set_cols:
            params[f"s_{k}"] = row.get(k)

        for i, (k, v) in enumerate(where_filters.items()):
            pname = f"w_{i}"
            if v is None:
                where_sql_parts.append(f"{_quote_ident(k)} IS NULL")
            else:
                where_sql_parts.append(f"{_quote_ident(k)} = :{pname}")
                params[pname] = v

        sql = f"UPDATE {self._quoted} SET {set_sql} WHERE " + " AND ".join(where_sql_parts)
        cur = self.db.execute(sql, params)
        return int(cur.rowcount if cur.rowcount is not None else 0)

    def upsert(self, row: Dict[str, Any], keys: Union[str, Sequence[str]]) -> Any:
        if row is None or not isinstance(row, dict):
            raise TypeError("row must be a dict")
        key_cols = _normalize_columns(keys)
        if not key_cols:
            raise ValueError("keys must not be empty")

        self._ensure_columns_for_row(row)

        # If a matching row exists, update; else insert.
        filters = {k: row.get(k) for k in key_cols}
        existing = self.find_one(**filters)
        if existing is None:
            return self.insert(row)
        # Update; return existing id if available, else count updated.
        self.update(row, keys=key_cols)
        if "id" in existing:
            return existing["id"]
        return None

    def create_index(self, columns: Union[str, Sequence[str]]) -> None:
        self._ensure_table()
        cols = _normalize_columns(columns)
        if not cols:
            return

        # Create a real SQLite index for performance and also track in meta for has_index.
        idx_name = f"ix_{self.name}_" + "_".join(cols)
        idx_ident = _quote_ident(idx_name)
        cols_sql = ", ".join(_quote_ident(c) for c in cols)

        try:
            self.db.execute(f"CREATE INDEX IF NOT EXISTS {idx_ident} ON {self._quoted} ({cols_sql})")
        except sqlite3.OperationalError:
            # If names are odd or too long, fall back to meta tracking only.
            pass

        cols_key = ",".join(cols)
        try:
            self.db.execute(
                "INSERT OR IGNORE INTO __dataset_indexes__(table_name, columns) VALUES (:t, :c)",
                {"t": self.name, "c": cols_key},
            )
        except Exception:
            pass

    def has_index(self, columns: Union[str, Sequence[str]]) -> bool:
        self._ensure_table()
        cols = _normalize_columns(columns)
        if not cols:
            return False
        cols_key = ",".join(cols)

        # First check our meta table
        cur = self.db.execute(
            "SELECT 1 FROM __dataset_indexes__ WHERE table_name = :t AND columns = :c LIMIT 1",
            {"t": self.name, "c": cols_key},
        )
        if cur.fetchone() is not None:
            return True

        # Also introspect sqlite indexes (in case created externally)
        cur = self.db.execute(f"PRAGMA index_list({self._quoted})")
        idx_rows = cur.fetchall()
        for idx in idx_rows:
            idx_name = idx["name"]
            ccur = self.db.execute(f"PRAGMA index_info({_quote_ident(idx_name)})")
            idx_cols = [r["name"] for r in ccur.fetchall()]
            if tuple(idx_cols) == tuple(cols):
                return True
        return False