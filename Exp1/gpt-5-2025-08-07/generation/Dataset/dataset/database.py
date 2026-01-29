import sqlite3
import threading
from typing import Any, Dict, Iterable, Iterator, Optional

class Database:
    """
    A minimal database wrapper exposing a dataset-like API using sqlite3.
    """

    def __init__(self, url: str):
        self.url = url
        self._conn = self._connect_sqlite(url)
        # Row factory to provide mapping-like rows
        self._conn.row_factory = sqlite3.Row
        self._in_transaction = False
        # Autocommit by default to mimic dataset's behavior outside explicit transactions
        # sqlite3 autocommit is enabled when isolation_level is None
        self._conn.isolation_level = None
        self._lock = threading.RLock()

    def _connect_sqlite(self, url: str) -> sqlite3.Connection:
        if not url.startswith("sqlite://"):
            raise ValueError("Only sqlite URLs are supported (sqlite://).")
        path = url[len("sqlite://"):]
        # Accept "sqlite:///:memory:" literally
        if path == "/:memory:" or path == ":memory:" or path == "/":
            db_path = ":memory:"
        else:
            # Strip leading slashes to normalize paths like sqlite:////tmp/x.db or sqlite:///tmp/x.db
            if path.startswith("///"):
                db_path = path[2:]  # keep leading "/" for absolute paths
            elif path.startswith("//"):
                db_path = path[1:]  # keep leading "/" for absolute paths
            elif path.startswith("/"):
                db_path = path  # absolute path
            else:
                db_path = path  # relative path
        conn = sqlite3.connect(db_path, check_same_thread=False)
        # Pragmas for reasonable performance and behavior
        try:
            conn.execute("PRAGMA foreign_keys=ON")
        except Exception:
            pass
        return conn

    def __getitem__(self, name: str):
        """
        Return a Table object for the given name. Table is created lazily upon first write.
        """
        from .table import Table  # local import to avoid circular dependency at module level
        return Table(self, name)

    # Transaction control
    def begin(self) -> None:
        """
        Begin an explicit transaction. Subsequent operations will be part of the transaction
        until commit() or rollback() is called.
        """
        with self._lock:
            if not self._in_transaction:
                self._conn.execute("BEGIN")
                self._in_transaction = True

    def commit(self) -> None:
        """
        Commit the current transaction.
        """
        with self._lock:
            if self._in_transaction:
                try:
                    self._conn.execute("COMMIT")
                finally:
                    self._in_transaction = False

    def rollback(self) -> None:
        """
        Roll back the current transaction.
        """
        with self._lock:
            if self._in_transaction:
                try:
                    self._conn.execute("ROLLBACK")
                finally:
                    self._in_transaction = False

    def query(self, sql: str, **params) -> Iterator[Dict[str, Any]]:
        """
        Execute a raw SQL query and yield dict-like rows.
        """
        with self._lock:
            cur = self._conn.execute(sql, params or {})
            for row in cur:
                # sqlite3.Row can be directly converted to dict
                yield dict(row)

    # Internal helpers
    def _execute(self, sql: str, params: Optional[Iterable[Any]] = None) -> sqlite3.Cursor:
        with self._lock:
            if params is None:
                return self._conn.execute(sql)
            return self._conn.execute(sql, params)

    def _executemany(self, sql: str, seq_of_params: Iterable[Iterable[Any]]) -> sqlite3.Cursor:
        with self._lock:
            return self._conn.executemany(sql, seq_of_params)

    def close(self) -> None:
        with self._lock:
            try:
                if self._in_transaction:
                    # If there's an open transaction, rollback to avoid partial writes.
                    try:
                        self._conn.execute("ROLLBACK")
                    except Exception:
                        pass
                self._conn.close()
            finally:
                self._in_transaction = False