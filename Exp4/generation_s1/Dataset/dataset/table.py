from __future__ import annotations

import json
import re
import sqlite3
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple, Union


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _quote_ident(name: str) -> str:
    # Always quote to be safe (reserved words, spaces, etc.)
    name = str(name)
    return '"' + name.replace('"', '""') + '"'


def _normalize_columns(columns: Union[str, Sequence[str]]) -> Tuple[str, ...]:
    if isinstance(columns, str):
        return (columns,)
    return tuple(columns)


def _normalize_keys(keys: Union[str, Sequence[str]]) -> Tuple[str, ...]:
    if isinstance(keys, str):
        return (keys,)
    return tuple(keys)


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
    # everything else stored as TEXT
    return "TEXT"


def _adapt_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (bool, int, float, str, bytes, bytearray, memoryview)):
        # bool is fine as int-ish; sqlite3 will convert bool to int
        return value
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, separators=(",", ":"), sort_keys=True)
    return str(value)


class Table:
    def __init__(self, db: Any, name: str):
        self.db = db
        self.name = name
        self._columns_cache: Optional[List[str]] = None
        self._ensure_table()

    def _ensure_table(self) -> None:
        sql = f"""
        CREATE TABLE IF NOT EXISTS {_quote_ident(self.name)} (
            id INTEGER PRIMARY KEY AUTOINCREMENT
        )
        """
        self.db.conn.execute(sql)
        self.db._after_ddl_if_needed()
        self._columns_cache = None

    def _refresh_columns(self) -> List[str]:
        cur = self.db.conn.execute(f"PRAGMA table_info({_quote_ident(self.name)})")
        try:
            cols = [r["name"] for r in cur.fetchall()]
        finally:
            cur.close()
        self._columns_cache = cols
        return cols

    @property
    def columns(self) -> List[str]:
        if self._columns_cache is None:
            return self._refresh_columns()
        return list(self._columns_cache)

    def _ensure_columns(self, keys: Iterable[str], sample_row: Optional[Mapping[str, Any]] = None) -> bool:
        existing = set(self.columns)
        ddl_ran = False
        for k in keys:
            if k in existing:
                continue
            # choose a type if we have a sample value
            t = "TEXT"
            if sample_row is not None and k in sample_row:
                t = _infer_sqlite_type(sample_row.get(k))
            self.db.conn.execute(
                f"ALTER TABLE {_quote_ident(self.name)} ADD COLUMN {_quote_ident(k)} {t}"
            )
            ddl_ran = True
            existing.add(k)
        if ddl_ran:
            self.db._after_ddl_if_needed()
            self._columns_cache = None
        return ddl_ran

    def __len__(self) -> int:
        return self.count()

    def insert(self, row: Mapping[str, Any]) -> int:
        if row is None:
            row = {}
        row = dict(row)
        if row:
            self._ensure_columns(row.keys(), sample_row=row)
            cols = list(row.keys())
            values = [_adapt_value(row.get(c)) for c in cols]
            col_sql = ", ".join(_quote_ident(c) for c in cols)
            ph_sql = ", ".join("?" for _ in cols)
            sql = f"INSERT INTO {_quote_ident(self.name)} ({col_sql}) VALUES ({ph_sql})"
            cur = self.db.conn.execute(sql, values)
        else:
            cur = self.db.conn.execute(f"INSERT INTO {_quote_ident(self.name)} DEFAULT VALUES")
        try:
            return int(cur.lastrowid)
        finally:
            cur.close()

    def insert_many(self, rows: Iterable[Mapping[str, Any]], chunk_size: Optional[int] = None) -> None:
        if chunk_size is None:
            chunk_size = 1000
        buf: List[Dict[str, Any]] = []
        for r in rows:
            buf.append(dict(r))
            if len(buf) >= chunk_size:
                self._insert_many_chunk(buf)
                buf.clear()
        if buf:
            self._insert_many_chunk(buf)

    def _insert_many_chunk(self, rows: List[Dict[str, Any]]) -> None:
        if not rows:
            return
        # union keys across chunk
        keys_set = set()
        for r in rows:
            keys_set.update(r.keys())
        keys = sorted(keys_set)
        if keys:
            # ensure columns exist; choose types based on first non-None sample
            # (best-effort; SQLite is forgiving)
            for k in keys:
                if k in set(self.columns):
                    continue
                sample = None
                for r in rows:
                    if k in r and r[k] is not None:
                        sample = r[k]
                        break
                self._ensure_columns([k], sample_row={k: sample})
            col_sql = ", ".join(_quote_ident(c) for c in keys)
            ph_sql = ", ".join("?" for _ in keys)
            sql = f"INSERT INTO {_quote_ident(self.name)} ({col_sql}) VALUES ({ph_sql})"
            params = [tuple(_adapt_value(r.get(k)) for k in keys) for r in rows]
            self.db.conn.executemany(sql, params)
        else:
            # all empty dicts
            self.db.conn.executemany(
                f"INSERT INTO {_quote_ident(self.name)} DEFAULT VALUES",
                [()] * len(rows),
            )

    def _compile_where(self, filters: Mapping[str, Any]) -> Tuple[str, List[Any]]:
        if not filters:
            return "", []
        parts: List[str] = []
        params: List[Any] = []
        for k, v in filters.items():
            col = _quote_ident(k)
            if v is None:
                parts.append(f"{col} IS NULL")
            elif isinstance(v, (list, tuple, set)):
                vs = list(v)
                if not vs:
                    parts.append("1=0")
                else:
                    parts.append(f"{col} IN ({', '.join(['?'] * len(vs))})")
                    params.extend([_adapt_value(x) for x in vs])
            else:
                parts.append(f"{col} = ?")
                params.append(_adapt_value(v))
        return " WHERE " + " AND ".join(parts), params

    def all(self) -> Iterator[Mapping[str, Any]]:
        return self.find()

    def find(self, **filters: Any) -> Iterator[Mapping[str, Any]]:
        where_sql, params = self._compile_where(filters)
        sql = f"SELECT * FROM {_quote_ident(self.name)}{where_sql}"
        cur = self.db.conn.execute(sql, params)
        try:
            for row in cur:
                yield dict(row)
        finally:
            cur.close()

    def find_one(self, **filters: Any) -> Optional[Mapping[str, Any]]:
        where_sql, params = self._compile_where(filters)
        sql = f"SELECT * FROM {_quote_ident(self.name)}{where_sql} LIMIT 1"
        cur = self.db.conn.execute(sql, params)
        try:
            r = cur.fetchone()
            return dict(r) if r is not None else None
        finally:
            cur.close()

    def distinct(self, column: str) -> List[Any]:
        sql = f"SELECT DISTINCT {_quote_ident(column)} AS v FROM {_quote_ident(self.name)}"
        cur = self.db.conn.execute(sql)
        try:
            return [row["v"] for row in cur.fetchall()]
        finally:
            cur.close()

    def count(self, **filters: Any) -> int:
        where_sql, params = self._compile_where(filters)
        sql = f"SELECT COUNT(*) AS c FROM {_quote_ident(self.name)}{where_sql}"
        cur = self.db.conn.execute(sql, params)
        try:
            return int(cur.fetchone()["c"])
        finally:
            cur.close()

    def update(self, row: Mapping[str, Any], keys: Union[str, Sequence[str]]) -> int:
        row = dict(row)
        key_cols = _normalize_keys(keys)
        for k in key_cols:
            if k not in row:
                raise KeyError(f"Missing key column {k!r} in row")
        # ensure columns for any provided fields
        if row:
            self._ensure_columns(row.keys(), sample_row=row)

        set_cols = [c for c in row.keys() if c not in key_cols]
        if not set_cols:
            return 0

        set_sql = ", ".join(f"{_quote_ident(c)} = ?" for c in set_cols)
        where_sql = " AND ".join(f"{_quote_ident(k)} = ?" for k in key_cols)
        params = [_adapt_value(row[c]) for c in set_cols] + [_adapt_value(row[k]) for k in key_cols]
        sql = f"UPDATE {_quote_ident(self.name)} SET {set_sql} WHERE {where_sql}"
        cur = self.db.conn.execute(sql, params)
        try:
            return int(cur.rowcount if cur.rowcount is not None else 0)
        finally:
            cur.close()

    def upsert(self, row: Mapping[str, Any], keys: Union[str, Sequence[str]]) -> Any:
        n = self.update(row, keys)
        if n == 0:
            return self.insert(row)
        return n

    def delete(self, **filters: Any) -> int:
        where_sql, params = self._compile_where(filters)
        sql = f"DELETE FROM {_quote_ident(self.name)}{where_sql}"
        cur = self.db.conn.execute(sql, params)
        try:
            return int(cur.rowcount if cur.rowcount is not None else 0)
        finally:
            cur.close()

    def create_index(self, columns: Union[str, Sequence[str]]) -> None:
        cols = _normalize_columns(columns)
        # ensure cols exist (best-effort)
        self._ensure_columns(cols, sample_row={c: None for c in cols})
        idx_name = "ix_" + re.sub(r"[^A-Za-z0-9_]+", "_", f"{self.name}_" + "_".join(cols))
        col_sql = ", ".join(_quote_ident(c) for c in cols)
        sql = f"CREATE INDEX IF NOT EXISTS {_quote_ident(idx_name)} ON {_quote_ident(self.name)} ({col_sql})"
        self.db.conn.execute(sql)
        self.db._after_ddl_if_needed()

    def has_index(self, columns: Union[str, Sequence[str]]) -> bool:
        target = _normalize_columns(columns)
        # SQLite metadata check
        cur = self.db.conn.execute(f"PRAGMA index_list({_quote_ident(self.name)})")
        try:
            idxs = cur.fetchall()
        finally:
            cur.close()
        for idx in idxs:
            idx_name = idx["name"]
            c2 = self.db.conn.execute(f"PRAGMA index_info({_quote_ident(idx_name)})")
            try:
                infos = c2.fetchall()
            finally:
                c2.close()
            # 'seqno' gives order
            infos_sorted = sorted(infos, key=lambda r: r["seqno"])
            cols = tuple(r["name"] for r in infos_sorted)
            if cols == target:
                return True
        return False