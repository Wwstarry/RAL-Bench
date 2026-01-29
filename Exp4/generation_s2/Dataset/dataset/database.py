import sqlite3
import threading
from typing import Any, Dict, Iterable, Iterator, Optional

from .table import Table


def _parse_sqlite_url(url: str) -> str:
    if not isinstance(url, str):
        raise TypeError("url must be a string")
    if not url.startswith("sqlite:"):
        raise ValueError("Only sqlite URLs are supported in this lightweight implementation")

    # Accept forms:
    # sqlite:///:memory:
    # sqlite:////abs/path.db
    # sqlite:///rel/path.db
    # sqlite://rel/path.db
    if url in ("sqlite:///:memory:", "sqlite:///:memory:"):
        return ":memory:"

    rest = url[len("sqlite:") :]
    # rest begins with '//' for typical URLs
    if rest.startswith("////"):
        # absolute path (sqlite:////tmp/x.db -> /tmp/x.db)
        return rest[3:]
    if rest.startswith("///"):
        # relative path (sqlite:///x.db -> x.db)
        return rest[3:]
    if rest.startswith("//"):
        # sqlite://x.db -> x.db  (nonstandard but common in tests)
        return rest[2:]
    if rest.startswith("/"):
        # sqlite:/tmp/x.db
        return rest
    # sqlite:foo.db
    return rest


class Database:
    """
    Database wrapper around sqlite3 with a subset of the `dataset` API.
    """

    def __init__(self, url: str, **kwargs: Any):
        self.url = url
        self.path = _parse_sqlite_url(url)

        # One connection per Database instance; sqlite3 is threadsafe with check_same_thread=False.
        # Using isolation_level=None enables autocommit mode; we manage transactions explicitly.
        self._conn = sqlite3.connect(
            self.path,
            isolation_level=None,
            check_same_thread=False,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        self._conn.row_factory = sqlite3.Row

        self._lock = threading.RLock()
        self._tables: Dict[str, Table] = {}

        # Transaction tracking (BEGIN/COMMIT/ROLLBACK)
        self._in_transaction = False

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    def close(self) -> None:
        with self._lock:
            try:
                self._conn.close()
            except Exception:
                pass

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        # mimic dataset behavior: rollback on exception if inside transaction
        if exc_type is not None:
            try:
                if self._in_transaction:
                    self.rollback()
            finally:
                self.close()
            return
        try:
            if self._in_transaction:
                self.commit()
        finally:
            self.close()

    def __getitem__(self, name: str) -> Table:
        if not isinstance(name, str) or not name:
            raise KeyError("Table name must be a non-empty string")
        with self._lock:
            tbl = self._tables.get(name)
            if tbl is None:
                tbl = Table(self, name)
                self._tables[name] = tbl
            return tbl

    def begin(self) -> None:
        with self._lock:
            if self._in_transaction:
                return
            # BEGIN IMMEDIATE ensures write lock is acquired early.
            self._conn.execute("BEGIN")
            self._in_transaction = True

    def commit(self) -> None:
        with self._lock:
            if not self._in_transaction:
                return
            self._conn.execute("COMMIT")
            self._in_transaction = False

    def rollback(self) -> None:
        with self._lock:
            if not self._in_transaction:
                return
            self._conn.execute("ROLLBACK")
            self._in_transaction = False

    def query(self, sql: str, **params: Any) -> Iterator[Dict[str, Any]]:
        """
        Execute raw SQL with optional named parameters. Yields dict rows.
        """
        with self._lock:
            cur = self._conn.execute(sql, params or {})
            rows = cur.fetchall()
        for row in rows:
            yield dict(row)

    def execute(self, sql: str, params: Optional[Dict[str, Any]] = None) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.execute(sql, params or {})

    def executemany(self, sql: str, seq_of_params: Iterable[Dict[str, Any]]) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.executemany(sql, list(seq_of_params))


def connect(url: str, **kwargs: Any) -> Database:
    """
    Connect to a database URL. Only sqlite URLs are supported.
    """
    return Database(url, **kwargs)