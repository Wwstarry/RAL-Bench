from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Iterator, Mapping, Optional, Tuple

from .table import Table


def _parse_sqlite_url(url: str) -> str:
    if not isinstance(url, str) or "://" not in url:
        raise ValueError(f"Invalid URL: {url!r}")
    scheme, rest = url.split("://", 1)
    if scheme != "sqlite":
        raise ValueError(f"Unsupported scheme: {scheme!r}")
    # sqlite:///:memory:
    if rest == "/:memory:":
        return ":memory:"
    # sqlite:////absolute/path -> rest startswith "///"
    # sqlite:///relative/path -> rest startswith "//"
    # Given split at "://", rest includes the leading slashes.
    # Examples:
    #   sqlite:////tmp/x.db -> rest == "//tmp/x.db"
    #   sqlite:///x.db -> rest == "/x.db"
    if rest.startswith("///"):
        # rare; keep conservative
        return rest[2:]  # drop two slashes, keep absolute leading slash
    if rest.startswith("//"):
        return rest[1:]  # drop one slash, keep absolute leading slash
    if rest.startswith("/"):
        return rest[1:]  # relative path
    return rest


@dataclass
class _DDLResult:
    ddl_ran: bool = False


class Database:
    def __init__(self, url: str):
        self.url = url
        self.path = _parse_sqlite_url(url)

        self.conn = sqlite3.connect(
            self.path,
            isolation_level=None,  # manual transaction control
            check_same_thread=True,
        )
        self.conn.row_factory = sqlite3.Row

        # local state
        self._tables: Dict[str, Table] = {}
        self._in_transaction: bool = False

        # pragmatic defaults for performance without changing semantics
        with self.conn:
            self.conn.execute("PRAGMA foreign_keys=ON")
            self.conn.execute("PRAGMA journal_mode=WAL" if self.path != ":memory:" else "PRAGMA journal_mode=MEMORY")
            self.conn.execute("PRAGMA synchronous=NORMAL")

    def __getitem__(self, name: str) -> Table:
        if name not in self._tables:
            self._tables[name] = Table(self, name)
        return self._tables[name]

    def begin(self) -> None:
        if not self._in_transaction:
            self.conn.execute("BEGIN")
            self._in_transaction = True

    def commit(self) -> None:
        if self._in_transaction:
            self.conn.execute("COMMIT")
            self._in_transaction = False

    def rollback(self) -> None:
        if self._in_transaction:
            self.conn.execute("ROLLBACK")
            self._in_transaction = False

    def _after_ddl_if_needed(self) -> None:
        # SQLite may auto-commit around DDL. If user requested an explicit
        # transaction, restore transactional mode for subsequent DML.
        if self._in_transaction:
            # If already in a transaction, BEGIN will error. Try to detect quickly.
            # sqlite3 doesn't expose transaction state reliably; just attempt BEGIN
            # and ignore the error.
            try:
                self.conn.execute("BEGIN")
            except sqlite3.OperationalError:
                pass

    def query(self, sql: str, **params: Any) -> Iterator[Mapping[str, Any]]:
        cur = self.conn.execute(sql, params)
        try:
            for row in cur:
                yield dict(row)
        finally:
            cur.close()