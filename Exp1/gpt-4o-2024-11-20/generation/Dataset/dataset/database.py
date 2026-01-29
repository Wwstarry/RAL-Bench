# dataset/database.py

import sqlite3
from .table import Table

class Database:
    def __init__(self, url):
        if not url.startswith("sqlite://"):
            raise ValueError("Only SQLite databases are supported.")
        self.connection = sqlite3.connect(url.split("://")[1], isolation_level=None)
        self.connection.row_factory = sqlite3.Row
        self._transaction_active = False

    def __getitem__(self, name):
        return Table(self.connection, name)

    def begin(self):
        if self._transaction_active:
            raise RuntimeError("Transaction already active.")
        self.connection.execute("BEGIN")
        self._transaction_active = True

    def commit(self):
        if not self._transaction_active:
            raise RuntimeError("No active transaction.")
        self.connection.execute("COMMIT")
        self._transaction_active = False

    def rollback(self):
        if not self._transaction_active:
            raise RuntimeError("No active transaction.")
        self.connection.execute("ROLLBACK")
        self._transaction_active = False

    def query(self, sql, **params):
        cursor = self.connection.execute(sql, params)
        for row in cursor:
            yield dict(row)

def connect(url):
    return Database(url)