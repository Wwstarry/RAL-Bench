import sqlite3
from .table import Table


def connect(url):
    """
    Connect to the database specified by the url.
    Currently only supports sqlite:// URLs.
    """
    if not url.startswith("sqlite:///"):
        raise ValueError("Only sqlite URLs supported, e.g. sqlite:///:memory:")
    path = url[len("sqlite:///"):]
    conn = sqlite3.connect(path, isolation_level=None, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    return Database(conn)


class Database:
    def __init__(self, connection):
        self._conn = connection
        self._transaction_active = False

    def __getitem__(self, name):
        return Table(self, name)

    def begin(self):
        if self._transaction_active:
            # Nested transactions not supported, ignore
            return
        self._conn.execute("BEGIN")
        self._transaction_active = True

    def commit(self):
        if not self._transaction_active:
            return
        self._conn.execute("COMMIT")
        self._transaction_active = False

    def rollback(self):
        if not self._transaction_active:
            return
        self._conn.execute("ROLLBACK")
        self._transaction_active = False

    def query(self, sql, **params):
        cursor = self._conn.execute(sql, params)
        for row in cursor:
            yield dict(row)