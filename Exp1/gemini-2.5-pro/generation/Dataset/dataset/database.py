import sqlite3
from urllib.parse import urlparse, unquote
from .table import Table

def connect(url='sqlite:///:memory:', **kwargs):
    """
    Opens a new connection to a database.

    The URL is in the format of `dialect://user:password@host/database`.
    This implementation only supports the `sqlite` dialect.

    :param url: A database URL.
    :return: A Database instance.
    """
    parsed_url = urlparse(url)
    scheme = parsed_url.scheme.lower()

    if scheme not in ('sqlite',):
        raise ValueError(f"Unsupported database scheme: {scheme}")

    # For sqlite:///:memory: path is ':memory:'
    # For sqlite:///path/to/db.sqlite, path is '/path/to/db.sqlite'
    db_path = unquote(parsed_url.path)
    if db_path.startswith('/'):
        db_path = db_path[1:]

    conn = sqlite3.connect(db_path, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    # Set isolation_level to None for autocommit mode, which we will
    # override with explicit BEGIN/COMMIT/ROLLBACK calls.
    conn.isolation_level = None
    return Database(conn)


class Database:
    """
    Represents a database connection.
    Provides access to tables and transaction control.
    """
    def __init__(self, connection):
        self.conn = connection
        self._tables = {}
        self._transaction_active = False

    def __getitem__(self, name):
        """
        Get a table by name. This is the standard way to access tables.
        If the table does not exist, it will be created upon first insert.

        :param name: The name of the table.
        :return: A Table instance.
        """
        if name not in self._tables:
            self._tables[name] = Table(self, name)
        return self._tables[name]

    def begin(self):
        """
        Begin a new transaction.
        """
        if not self._transaction_active:
            self.conn.execute("BEGIN")
            self._transaction_active = True

    def commit(self):
        """
        Commit the current transaction.
        """
        if self._transaction_active:
            self.conn.execute("COMMIT")
            self._transaction_active = False

    def rollback(self):
        """
        Roll back the current transaction.
        """
        if self._transaction_active:
            self.conn.execute("ROLLBACK")
            self._transaction_active = False

    def query(self, sql, **params):
        """
        Execute a raw SQL query and yield rows as dictionaries.

        :param sql: The SQL query string.
        :param params: A dictionary of parameters to bind to the query.
        """
        cursor = self.conn.cursor()
        cursor.execute(sql, params)
        for row in cursor:
            yield dict(row)

    def __repr__(self):
        return f"<Database(connection={self.conn})>"