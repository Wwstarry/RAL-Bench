"""
Database connection and management
"""

import sqlite3
from urllib.parse import urlparse
from dataset.table import Table


class Database:
    """
    Represents a database connection with table access and transaction support.
    """
    
    def __init__(self, url):
        """
        Initialize a database connection.
        
        Args:
            url: Database URL (currently only supports sqlite://)
        """
        self.url = url
        self._connection = None
        self._tables = {}
        self._in_transaction = False
        self._connect()
    
    def _connect(self):
        """Establish the database connection."""
        parsed = urlparse(self.url)
        
        if parsed.scheme != 'sqlite':
            raise ValueError(f"Unsupported database scheme: {parsed.scheme}")
        
        # Handle in-memory database
        if parsed.path == '/:memory:':
            db_path = ':memory:'
        else:
            db_path = parsed.path.lstrip('/')
        
        self._connection = sqlite3.connect(db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        # Enable autocommit by default (isolation_level=None)
        # We'll manage transactions explicitly
        self._connection.isolation_level = None
    
    def __getitem__(self, name):
        """
        Get or create a table by name.
        
        Args:
            name: Table name
        
        Returns:
            Table instance
        """
        if name not in self._tables:
            self._tables[name] = Table(self, name)
        return self._tables[name]
    
    def begin(self):
        """Begin a transaction."""
        if not self._in_transaction:
            self._connection.execute('BEGIN')
            self._in_transaction = True
    
    def commit(self):
        """Commit the current transaction."""
        if self._in_transaction:
            self._connection.commit()
            self._in_transaction = False
    
    def rollback(self):
        """Rollback the current transaction."""
        if self._in_transaction:
            self._connection.rollback()
            self._in_transaction = False
    
    def query(self, sql, **params):
        """
        Execute a SQL query and yield results as dictionaries.
        
        Args:
            sql: SQL query string
            **params: Query parameters
        
        Yields:
            Dictionary for each row
        """
        cursor = self._connection.execute(sql, params)
        for row in cursor:
            yield dict(row)
    
    def execute(self, sql, params=None):
        """
        Execute a SQL statement.
        
        Args:
            sql: SQL statement
            params: Parameters (dict or tuple)
        
        Returns:
            Cursor object
        """
        if params is None:
            params = {}
        return self._connection.execute(sql, params)
    
    def table_exists(self, name):
        """
        Check if a table exists.
        
        Args:
            name: Table name
        
        Returns:
            True if table exists, False otherwise
        """
        cursor = self._connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
            (name,)
        )
        return cursor.fetchone() is not None
    
    def get_table_columns(self, name):
        """
        Get column names for a table.
        
        Args:
            name: Table name
        
        Returns:
            List of column names
        """
        if not self.table_exists(name):
            return []
        
        cursor = self._connection.execute(f"PRAGMA table_info({name})")
        return [row[1] for row in cursor]
    
    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None