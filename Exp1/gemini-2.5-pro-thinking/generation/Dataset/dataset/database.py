"""
This module contains the Database class and the connect() function,
which are the main entry points for interacting with a database.
"""
import sqlalchemy
from sqlalchemy.engine import Engine
from .table import Table

class Database(object):
    """
    Represents a database connection.
    
    Provides access to tables and transaction control.
    """
    def __init__(self, engine):
        if not isinstance(engine, Engine):
            raise TypeError("Expected a SQLAlchemy Engine")
        self.engine = engine
        self.metadata = sqlalchemy.MetaData()
        self.metadata.bind = self.engine
        self._tables = {}
        self._tx = None
        self._conn = None

    def __getitem__(self, name):
        """Get a table by name. Tables are created lazily."""
        if name not in self._tables:
            self._tables[name] = Table(self, name)
        return self._tables[name]

    def __repr__(self):
        return f"<Database({self.engine.url!r})>"

    def _get_connection(self):
        """
        Get the current transactional connection, or a new one from the engine.
        """
        if self._conn:
            return self._conn
        return self.engine.connect()

    def begin(self):
        """Start a new transaction."""
        if self._tx is not None:
            raise RuntimeError("Transaction already started.")
        self._conn = self.engine.connect()
        self._tx = self._conn.begin()

    def commit(self):
        """Commit the current transaction."""
        if self._tx is None:
            raise RuntimeError("Not in a transaction.")
        self._tx.commit()
        self._close_transaction()

    def rollback(self):
        """Roll back the current transaction."""
        if self._tx is None:
            raise RuntimeError("Not in a transaction.")
        self._tx.rollback()
        self._close_transaction()

    def _close_transaction(self):
        """Clean up transaction state."""
        if self._conn:
            self._conn.close()
        self._conn = None
        self._tx = None

    def query(self, sql, **params):
        """
        Execute a raw SQL query and yield rows as dictionaries.
        """
        conn = self._get_connection()
        try:
            # Use future=True style execution for mapping-like rows
            result = conn.execute(sqlalchemy.text(sql), params)
            for row in result.mappings():
                yield dict(row)
        finally:
            if not self._tx:
                conn.close()

def connect(url="sqlite:///:memory:", **kwargs):
    """
    Connect to a database.

    Args:
        url (str): A database URL, e.g., 'sqlite:///mydatabase.db'
                   or 'sqlite:///:memory:'.
        **kwargs: Additional arguments passed to SQLAlchemy's create_engine.

    Returns:
        Database: A Database instance.
    """
    engine = sqlalchemy.create_engine(url, **kwargs)
    return Database(engine)