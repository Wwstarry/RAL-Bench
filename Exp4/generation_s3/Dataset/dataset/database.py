import sqlite3
import threading
from typing import Any, Dict, Iterable, Iterator, Mapping, Optional

from .table import Table


def _parse_sqlite_url(url: str) -> str:
    # Supported:
    # - sqlite:///:memory:
    # - sqlite:////absolute/path.db
    # - sqlite:///relative/path.db
    # - sqlite://relative/path.db (treat as relative)
    if not isinstance(url, str):
        raise TypeError("url must be a string")
    if "\x00" in url:
        raise ValueError("NUL byte in url")

    if not url.startswith("sqlite:"):
        raise ValueError("Only sqlite URLs are supported")

    rest = url[len("sqlite:") :]

    # Exact in-memory canonical form
    if rest == "///:memory:":
        return ":memory:"

    # If starts with "////" => absolute path with leading slash
    # sqlite:////tmp/x.db -> /tmp/x.db
    if rest.startswith("////"):
        return rest[3:]  # keep one leading slash

    # sqlite:///relative/path.db -> relative/path.db
    if rest.startswith("///"):
        return rest[3:]

    # sqlite://relative/path.db -> relative/path.db (non-standard but lenient)
    if rest.startswith("//"):
        return rest[2:]

    # sqlite:path.db -> path.db
    if rest.startswith("/"):
        # sqlite:/abs/path.db (rare)
        return rest
    return rest


class Database:
    def __init__(self, url: str, **kwargs: Any):
        self.url = url
        self._path = _parse_sqlite_url(url)

        # isolation_level=None puts sqlite3 in autocommit mode; we manage BEGIN/COMMIT ourselves.
        self._conn = sqlite3.connect(
            self._path,
            isolation_level=None,
            check_same_thread=True,
        )
        self._conn.row_factory = sqlite3.Row

        self._tables: Dict[str, Table] = {}
        self._in_transaction = False

        # lightweight lock for internal state; tests are single-threaded but keep consistent
        self._lock = threading.RLock()

    def close(self) -> None:
        with self._lock:
            try:
                self._conn.close()
            finally:
                self._tables.clear()

    def __getitem__(self, name: str) -> Table:
        if not isinstance(name, str) or not name:
            raise KeyError("Table name must be a non-empty string")
        if "\x00" in name:
            raise ValueError("NUL byte in table name")

        with self._lock:
            tbl = self._tables.get(name)
            if tbl is None:
                tbl = Table(self, name)
                self._tables[name] = tbl
            return tbl

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    @property
    def in_transaction(self) -> bool:
        return self._in_transaction

    def begin(self) -> None:
        with self._lock:
            if self._in_transaction:
                return
            cur = self._conn.cursor()
            try:
                cur.execute("BEGIN")
            finally:
                cur.close()
            self._in_transaction = True

    def commit(self) -> None:
        with self._lock:
            if not self._in_transaction:
                return
            cur = self._conn.cursor()
            try:
                cur.execute("COMMIT")
            finally:
                cur.close()
            self._in_transaction = False

    def rollback(self) -> None:
        with self._lock:
            if not self._in_transaction:
                return
            cur = self._conn.cursor()
            try:
                cur.execute("ROLLBACK")
            finally:
                cur.close()
            self._in_transaction = False

    def execute(self, sql: str, params: Optional[Mapping[str, Any]] = None) -> sqlite3.Cursor:
        # For internal use: returns cursor (caller should close).
        cur = self._conn.cursor()
        if params is None:
            cur.execute(sql)
        else:
            cur.execute(sql, dict(params))
        return cur

    def query(self, sql: str, **params: Any) -> Iterator[Mapping[str, Any]]:
        # Execute any SQL; if it returns rows, yield row dicts.
        # For non-SELECT queries, yield nothing but still execute.
        cur = self._conn.cursor()
        try:
            cur.execute(sql, params or {})
            if cur.description is None:
                return iter(())
            cols = [d[0] for d in cur.description]

            def gen() -> Iterator[Mapping[str, Any]]:
                try:
                    for r in cur:
                        # sqlite3.Row supports mapping; convert to plain dict for compatibility
                        yield {cols[i]: r[i] for i in range(len(cols))}
                finally:
                    cur.close()

            return gen()
        except Exception:
            cur.close()
            raise


def connect(url: str, **kwargs: Any) -> Database:
    return Database(url, **kwargs)