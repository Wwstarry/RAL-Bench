"""
Database connection and transaction management.
"""

import sqlite3
import threading
from typing import Dict, Iterator, Optional, Any
from urllib.parse import urlparse

from dataset.table import Table


class Database:
    """Database connection with transaction support."""
    
    def __init__(self, url: str):
        """
        Initialize database connection.
        
        Args:
            url: Database URL (only sqlite:// is supported)
        """
        parsed = urlparse(url)
        if parsed.scheme != "sqlite":
            raise ValueError(f"Unsupported database scheme: {parsed.scheme}")
        
        # Extract database path (remove leading //)
        db_path = parsed.netloc + parsed.path
        if db_path.startswith("//"):
            db_path = db_path[2:]
        if db_path == ":memory:":
            db_path = ":memory:"
        
        self.url = url
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._tables: Dict[str, Table] = {}
        self._lock = threading.RLock()
        self._in_transaction = False
        
    def __getitem__(self, name: str) -> Table:
        """
        Get or create a table by name.
        
        Args:
            name: Table name
            
        Returns:
            Table instance
        """
        with self._lock:
            if name not in self._tables:
                self._tables[name] = Table(self, name)
            return self._tables[name]
    
    def begin(self) -> None:
        """Begin a transaction."""
        with self._lock:
            if self._in_transaction:
                raise RuntimeError("Already in a transaction")
            self._conn.execute("BEGIN")
            self._in_transaction = True
    
    def commit(self) -> None:
        """Commit the current transaction."""
        with self._lock:
            if not self._in_transaction:
                raise RuntimeError("Not in a transaction")
            self._conn.commit()
            self._in_transaction = False
    
    def rollback(self) -> None:
        """Rollback the current transaction."""
        with self._lock:
            if not self._in_transaction:
                raise RuntimeError("Not in a transaction")
            self._conn.rollback()
            self._in_transaction = False
    
    def query(self, sql: str, **params: Any) -> Iterator[Dict[str, Any]]:
        """
        Execute a SQL query and yield rows as dictionaries.
        
        Args:
            sql: SQL query string
            **params: Query parameters
            
        Yields:
            Rows as dictionaries
        """
        with self._lock:
            cursor = self._conn.execute(sql, params)
            for row in cursor:
                yield dict(row)
    
    def execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        """
        Execute SQL statement.
        
        Args:
            sql: SQL statement
            params: Parameters for the statement
            
        Returns:
            SQLite cursor
        """
        with self._lock:
            return self._conn.execute(sql, params)
    
    def executemany(self, sql: str, params_list: list) -> sqlite3.Cursor:
        """
        Execute SQL statement multiple times.
        
        Args:
            sql: SQL statement
            params_list: List of parameter tuples
            
        Returns:
            SQLite cursor
        """
        with self._lock:
            return self._conn.executemany(sql, params_list)
    
    def close(self) -> None:
        """Close the database connection."""
        with self._lock:
            self._conn.close()
    
    def __enter__(self):
        """Context manager entry."""
        self.begin()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is not None:
            self.rollback()
        else:
            self.commit()
    
    @property
    def connection(self) -> sqlite3.Connection:
        """Get the underlying SQLite connection."""
        return self._conn