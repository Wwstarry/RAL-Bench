# dataset/database.py
import sqlite3
from urllib.parse import urlparse
import json
from .table import Table

class Database:
    """A database connection."""
    
    def __init__(self, url, **kwargs):
        """Initialize a database connection.
        
        Args:
            url (str): Database connection URL
            **kwargs: Additional parameters to pass to the database
        """
        parsed_url = urlparse(url)
        self.scheme = parsed_url.scheme
        
        if self.scheme != 'sqlite':
            raise ValueError(f"Unsupported database type: {self.scheme}")
        
        if parsed_url.netloc == '' and parsed_url.path == '/:memory:':
            # In-memory SQLite database
            self.path = ':memory:'
        else:
            # File-based SQLite database
            self.path = parsed_url.path.lstrip('/')
        
        self.conn = sqlite3.connect(self.path)
        # Enable dictionary access to rows
        self.conn.row_factory = sqlite3.Row
        
        # Dictionary to cache tables
        self._tables = {}
        
        # Flag to track if we're in a transaction
        self._in_transaction = False
    
    def __getitem__(self, name):
        """Get a table by name.
        
        Args:
            name (str): The name of the table
            
        Returns:
            Table: The table object
        """
        if name not in self._tables:
            self._tables[name] = Table(self, name)
        return self._tables[name]
    
    def begin(self):
        """Begin a transaction."""
        if not self._in_transaction:
            self.conn.execute('BEGIN TRANSACTION')
            self._in_transaction = True
    
    def commit(self):
        """Commit the current transaction."""
        if self._in_transaction:
            self.conn.commit()
            self._in_transaction = False
    
    def rollback(self):
        """Roll back the current transaction."""
        if self._in_transaction:
            self.conn.rollback()
            self._in_transaction = False
    
    def query(self, sql, **params):
        """Execute a SQL query and return the results.
        
        Args:
            sql (str): The SQL query to execute
            **params: Parameters to bind to the query
            
        Yields:
            dict: The rows from the query
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute(sql, params)
            for row in cursor:
                yield dict(row)
        finally:
            cursor.close()
    
    def close(self):
        """Close the database connection."""
        self.conn.close()
        self._tables = {}