"""
Database connection and management.
"""

import sqlite3
from contextlib import contextmanager
from urllib.parse import urlparse

from dataset.table import Table


class Database:
    """
    Represents a database connection and provides access to tables.
    """
    
    def __init__(self, url):
        """
        Initialize a database connection.
        
        Args:
            url: Database URL (e.g., 'sqlite:///:memory:' or 'sqlite:///path/to/db.db')
        """
        self.url = url
        self._connection = None
        self._tables = {}
        self._in_transaction = False
        self._parse_url(url)
    
    def _parse_url(self, url):
        """Parse the database URL and establish connection."""
        parsed = urlparse(url)
        
        if parsed.scheme == 'sqlite':
            # Handle sqlite:// URLs
            if parsed.netloc:
                # sqlite://hostname/path format
                db_path = parsed.netloc + parsed.path
            else:
                # sqlite:///path format
                db_path = parsed.path
            
            # Handle :memory: special case
            if db_path == '/:memory:' or db_path == ':memory:':
                db_path = ':memory:'
            
            self._connection = sqlite3.connect(db_path, check_same_thread=False)
            self._connection.isolation_level = None  # Autocommit mode by default
        else:
            raise ValueError(f"Unsupported database scheme: {parsed.scheme}")
    
    def __getitem__(self, name):
        """
        Get or create a table by name.
        
        Args:
            name: Table name
        
        Returns:
            A Table instance.
        """
        if name not in self._tables:
            self._tables[name] = Table(self, name)
        return self._tables[name]
    
    def begin(self):
        """Start an explicit transaction."""
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
        Execute a raw SQL query and yield row mappings.
        
        Args:
            sql: SQL query string
            **params: Query parameters
        
        Yields:
            Row dictionaries.
        """
        cursor = self._connection.cursor()
        cursor.row_factory = sqlite3.Row
        cursor.execute(sql, params)
        for row in cursor.fetchall():
            yield dict(row)
    
    def execute(self, sql, params=None):
        """
        Execute a raw SQL statement.
        
        Args:
            sql: SQL statement
            params: Query parameters (optional)
        
        Returns:
            Cursor object.
        """
        if params is None:
            params = {}
        return self._connection.execute(sql, params)
    
    def executescript(self, sql):
        """
        Execute multiple SQL statements.
        
        Args:
            sql: SQL script
        """
        return self._connection.executescript(sql)
    
    def close(self):
        """Close the database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()