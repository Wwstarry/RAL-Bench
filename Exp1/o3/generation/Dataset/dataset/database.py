"""
Database abstraction wrapping a SQLite connection.
"""
from __future__ import annotations

import sqlite3
from typing import Dict, Iterator, Any, Optional

from .table import Table


class Database:
    """
    A very small subset of the public ``dataset.Database`` API.
    """

    def __init__(self, filename: str = ":memory:", **kwargs):
        # Ensure we control transactions manually.
        # isolation_level=None puts the connection in autocommit = False,
        # but allows explicit BEGIN.
        self._conn: sqlite3.Connection = sqlite3.connect(
            filename, detect_types=sqlite3.PARSE_DECLTYPES, isolation_level=None
        )
        # Use sqlite Row objects which are mapping-like.
        self._conn.row_factory = sqlite3.Row
        self._tables: Dict[str, Table] = {}
        self._in_transaction: bool = False

        # Pragmas to improve concurrency/performance for tests.
        cur = self._conn.cursor()
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()

    # ---------------------------------------------------------------------
    # Transaction helpers
    # ---------------------------------------------------------------------
    def begin(self) -> None:
        """
        Begin an explicit transaction.
        """
        if self._in_transaction:
            return
        self._conn.execute("BEGIN")
        self._in_transaction = True

    def commit(self) -> None:
        """
        Commit the current transaction.
        """
        if not self._in_transaction:
            return
        self._conn.execute("COMMIT")
        self._in_transaction = False

    def rollback(self) -> None:
        """
        Rollback the current transaction.
        """
        if not self._in_transaction:
            return
        self._conn.execute("ROLLBACK")
        self._in_transaction = False

    # ---------------------------------------------------------------------
    # Core API
    # ---------------------------------------------------------------------
    def __getitem__(self, name: str) -> Table:
        """
        Return a :class:`~dataset.table.Table` handle for *name*.
        The underlying table is created lazily on first demand.
        """
        if name not in self._tables:
            self._tables[name] = Table(self, name)
        return self._tables[name]

    def query(self, sql: str, **params) -> Iterator[dict]:
        """
        Execute *sql* and yield each row mapping.
        """
        cur = self._conn.execute(sql, params or {})
        columns = [col[0] for col in cur.description]
        for row in cur:
            # Convert sqlite3.Row to regular dict for compatibility.
            yield {col: row[idx] for idx, col in enumerate(columns)}

    # ---------------------------------------------------------------------
    # Context manager helpers (optional convenience)
    # ---------------------------------------------------------------------
    def __enter__(self) -> "Database":
        self.begin()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> Optional[bool]:
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        # Returning False will propagate exception if any.
        return False

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------
    @property
    def connection(self) -> sqlite3.Connection:
        """Expose the raw sqlite3 connection (internal use)."""
        return self._conn

    def close(self) -> None:
        """
        Close the underlying DB connection.
        """
        if self._conn:
            if self._in_transaction:
                self.rollback()
            self._conn.close()