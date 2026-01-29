import sqlite3
from typing import Dict, Iterator, Optional, Union
from .table import Table

class Database:
    def __init__(self, url: str):
        self.url = url
        self.conn = sqlite3.connect(url)
        self.conn.row_factory = sqlite3.Row
        self._tables: Dict[str, Table] = {}
        self._in_transaction = False

    def __getitem__(self, name: str) -> Table:
        if name not in self._tables:
            self._tables[name] = Table(self, name)
        return self._tables[name]

    def begin(self):
        if self._in_transaction:
            raise RuntimeError("Transaction already in progress")
        self._in_transaction = True
        self.conn.execute("BEGIN")

    def commit(self):
        if not self._in_transaction:
            raise RuntimeError("No transaction in progress")
        self.conn.commit()
        self._in_transaction = False

    def rollback(self):
        if not self._in_transaction:
            raise RuntimeError("No transaction in progress")
        self.conn.rollback()
        self._in_transaction = False

    def query(self, sql: str, **params) -> Iterator[dict]:
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        for row in cursor:
            yield dict(row)

    def close(self):
        self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def connect(url: str = "sqlite:///:memory:") -> Database:
    return Database(url)