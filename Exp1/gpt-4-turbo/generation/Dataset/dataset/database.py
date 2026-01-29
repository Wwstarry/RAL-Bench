import sqlite3
import threading
from contextlib import contextmanager
from .table import Table

_SQLITE_PREFIX = "sqlite://"

def connect(url):
    """
    Connect to a database. Only supports sqlite:// URLs.
    """
    if url.startswith(_SQLITE_PREFIX):
        path = url[len(_SQLITE_PREFIX):]
        if path == ":memory:":
            conn = sqlite3.connect(":memory:", check_same_thread=False, isolation_level=None)
        else:
            conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
        return Database(conn)
    raise ValueError("Only sqlite:// URLs are supported in this implementation.")

class Database:
    """
    Represents a database connection.
    """
    def __init__(self, connection):
        self._conn = connection
        self._lock = threading.RLock()
        self._transaction_active = False
        self._tables = {}

    def __getitem__(self, name):
        """
        Get a Table object for the given table name.
        """
        with self._lock:
            if name not in self._tables:
                self._tables[name] = Table(self, name)
            return self._tables[name]

    def begin(self):
        """
        Begin a transaction.
        """
        with self._lock:
            if not self._transaction_active:
                self._conn.execute("BEGIN")
                self._transaction_active = True

    def commit(self):
        """
        Commit the current transaction.
        """
        with self._lock:
            if self._transaction_active:
                self._conn.execute("COMMIT")
                self._transaction_active = False

    def rollback(self):
        """
        Rollback the current transaction.
        """
        with self._lock:
            if self._transaction_active:
                self._conn.execute("ROLLBACK")
                self._transaction_active = False

    def query(self, sql, **params):
        """
        Execute a raw SQL query and yield row dicts.
        """
        with self._lock:
            cursor = self._conn.execute(sql, params)
            columns = [desc[0] for desc in cursor.description]
            for row in cursor:
                yield dict(zip(columns, row))

    @property
    def connection(self):
        return self._conn

    def __del__(self):
        try:
            self._conn.close()
        except Exception:
            pass