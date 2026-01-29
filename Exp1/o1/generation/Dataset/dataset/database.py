import sqlite3

from .table import Table

class Database:
    """
    A lightweight database object wrapping a sqlite3 connection and
    providing API-compatible methods for dataset usage.
    """

    def __init__(self, connection):
        self._connection = connection
        self._transaction_active = False
        self._tables = {}

    def __getitem__(self, name):
        """
        Return a Table object for the given table name.
        Tables are created lazily.
        """
        if name not in self._tables:
            self._tables[name] = Table(self, name)
        return self._tables[name]

    def query(self, sql, **params):
        """
        Execute the given SQL with named parameters and yield dictionaries.
        """
        cur = self._connection.execute(sql, params)
        for row in cur:
            yield dict(row)

    def begin(self):
        """
        Start a transaction unless one is already active.
        """
        if not self._transaction_active:
            self._connection.execute('BEGIN')
            self._transaction_active = True

    def commit(self):
        """
        Commit the current transaction, if active.
        """
        if self._transaction_active:
            self._connection.execute('COMMIT')
            self._transaction_active = False

    def rollback(self):
        """
        Roll back the current transaction, if active.
        """
        if self._transaction_active:
            self._connection.execute('ROLLBACK')
            self._transaction_active = False