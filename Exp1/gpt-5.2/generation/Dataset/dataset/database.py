from __future__ import annotations

import re
import sqlite3
import threading
from contextlib import contextmanager
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple

from .table import Table


def _parse_sqlite_url(url: str) -> Tuple[str, bool]:
    """
    Return (sqlite_path, uri_flag) suitable for sqlite3.connect(path, uri=uri_flag).
    """
    if not isinstance(url, str):
        raise TypeError("url must be a string")
    if url == "sqlite:///:memory:":
        return ":memory:", False

    if url.startswith("sqlite:///"):
        # sqlite:////abs/path  OR sqlite:///rel/path
        path = url[len("sqlite:///") :]
        if path.startswith("/"):
            # Could be "/abs/path" or "//abs/path" (i.e. from sqlite:////abs/path)
            # sqlite URL with 4 slashes becomes path starting with "//"
            while path.startswith("//"):
                path = path[1:]
            return path, False
        return path, False

    if url.startswith("sqlite://"):
        path = url[len("sqlite://") :]
        if path == ":memory:":
            return ":memory:", False
        # allow file: URIs
        if path.startswith("file:"):
            return path, True
        return path, False

    raise ValueError(f"Unsupported database URL: {url}")


class Database:
    """
    Minimal Database implementation compatible with core parts of `dataset`.
    """

    def __init__(self, url: str, **kwargs: Any):
        self.url = url
        path, uri = _parse_sqlite_url(url)

        # Use autocommit mode (isolation_level=None) so BEGIN/COMMIT/ROLLBACK
        # are controlled explicitly and visible to tests.
        self._conn = sqlite3.connect(
            path,
            uri=uri,
            isolation_level=None,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row

        # Some pragmatic defaults
        try:
            self._conn.execute("PRAGMA foreign_keys=ON")
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
        except sqlite3.DatabaseError:
            pass

        self._tables: Dict[str, Table] = {}
        self._tx_depth = 0
        self._lock = threading.RLock()

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    def close(self) -> None:
        with self._lock:
            try:
                self._conn.close()
            finally:
                self._tables.clear()

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def __getitem__(self, name: str) -> Table:
        if not isinstance(name, str) or not name:
            raise KeyError("Table name must be a non-empty string")
        with self._lock:
            tbl = self._tables.get(name)
            if tbl is None:
                tbl = Table(self, name)
                self._tables[name] = tbl
            return tbl

    # --- Transactions ---
    def begin(self) -> None:
        with self._lock:
            if self._tx_depth == 0:
                self._conn.execute("BEGIN")
            else:
                self._conn.execute(f"SAVEPOINT sp_{self._tx_depth}")
            self._tx_depth += 1

    def commit(self) -> None:
        with self._lock:
            if self._tx_depth <= 0:
                return
            self._tx_depth -= 1
            if self._tx_depth == 0:
                self._conn.execute("COMMIT")
            else:
                self._conn.execute(f"RELEASE SAVEPOINT sp_{self._tx_depth}")

    def rollback(self) -> None:
        with self._lock:
            if self._tx_depth <= 0:
                return
            self._tx_depth -= 1
            if self._tx_depth == 0:
                self._conn.execute("ROLLBACK")
            else:
                self._conn.execute(f"ROLLBACK TO SAVEPOINT sp_{self._tx_depth}")
                self._conn.execute(f"RELEASE SAVEPOINT sp_{self._tx_depth}")

    @contextmanager
    def transaction(self) -> Iterator["Database"]:
        self.begin()
        try:
            yield self
            self.commit()
        except Exception:
            self.rollback()
            raise

    # --- Query helper ---
    _param_pat = re.compile(r":([A-Za-z_][A-Za-z0-9_]*)")

    def _coerce_params(self, sql: str, params: Mapping[str, Any]) -> Tuple[str, Dict[str, Any]]:
        # Keep named parameters as-is for sqlite. Ensure dict keys exist.
        needed = set(self._param_pat.findall(sql))
        if needed and not isinstance(params, dict):
            params = dict(params)
        missing = needed.difference(params.keys())
        if missing:
            raise ValueError(f"Missing SQL parameters: {sorted(missing)}")
        return sql, dict(params)

    def query(self, sql: str, **params: Any) -> Iterator[Mapping[str, Any]]:
        """Execute raw SQL and yield mapping rows (dict-like)."""
        with self._lock:
            sql2, p2 = self._coerce_params(sql, params)
            cur = self._conn.execute(sql2, p2)
            # If no rows, this is fine.
            colnames = [d[0] for d in cur.description] if cur.description else []
            for row in cur:
                if isinstance(row, sqlite3.Row):
                    yield dict(row)
                else:
                    yield dict(zip(colnames, row))

    def execute(self, sql: str, params: Optional[Mapping[str, Any]] = None) -> sqlite3.Cursor:
        with self._lock:
            if params is None:
                return self._conn.execute(sql)
            return self._conn.execute(sql, dict(params))

    def executemany(self, sql: str, seq_of_params: Sequence[Mapping[str, Any]]) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.executemany(sql, [dict(p) for p in seq_of_params])