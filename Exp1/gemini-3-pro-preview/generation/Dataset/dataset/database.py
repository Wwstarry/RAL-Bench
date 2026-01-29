import sqlite3
import threading
from urllib.parse import urlparse
from dataset.table import Table

class Database:
    def __init__(self, url, **kwargs):
        self.url = url
        self._tables = {}
        self.lock = threading.RLock()
        
        # Basic parsing for sqlite URLs to standard sqlite3 connection
        parsed = urlparse(url)
        if parsed.scheme.startswith('sqlite'):
            path = parsed.path
            if path.startswith('///'):
                path = path[3:]
            elif path.startswith('//'):
                path = path[2:]
            
            # Handle :memory: specifically or absolute paths
            if path == ':memory:' or 'mode=memory' in parsed.query:
                db_path = ':memory:'
            else:
                # Remove leading slash for relative paths if necessary, 
                # though usually sqlite:///foo.db means foo.db in current dir
                if path.startswith('/'):
                    db_path = path[1:]
                else:
                    db_path = path

            self._conn = sqlite3.connect(db_path, check_same_thread=False, **kwargs)
            # Enable name-based access to columns
            self._conn.row_factory = sqlite3.Row
        else:
            raise NotImplementedError("Only sqlite:// schemes are supported in this lightweight implementation.")

    @property
    def tables(self):
        """Get a list of table names in the database."""
        q = "SELECT name FROM sqlite_master WHERE type='table'"
        return [r['name'] for r in self.query(q)]

    def __getitem__(self, table_name):
        """
        Get a table object by name. Creates the object wrapper, 
        but the actual DB table is created lazily on write.
        """
        with self.lock:
            if table_name not in self._tables:
                self._tables[table_name] = Table(self, table_name)
            return self._tables[table_name]

    def __contains__(self, table_name):
        return table_name in self.tables

    def query(self, query, **params):
        """
        Execute a raw SQL query.
        
        Args:
            query (str): The SQL query.
            **params: Parameters to bind to the query.
            
        Yields:
            dict: Rows as dictionaries.
        """
        with self.lock:
            cursor = self._conn.cursor()
            try:
                # SQLite supports :name style parameters
                cursor.execute(query, params)
                # If it's a select, yield rows
                if cursor.description:
                    for row in cursor:
                        yield dict(row)
            finally:
                cursor.close()

    def begin(self):
        """Begin a transaction."""
        with self.lock:
            # SQLite starts transactions implicitly, but we can force it
            # or ensure we aren't in autocommit mode.
            # Standard sqlite3 module handles this via isolation_level, 
            # but explicit BEGIN is safer for API compatibility.
            self._conn.execute("BEGIN")

    def commit(self):
        """Commit the current transaction."""
        with self.lock:
            self._conn.commit()

    def rollback(self):
        """Rollback the current transaction."""
        with self.lock:
            self._conn.rollback()

    def close(self):
        """Close the database connection."""
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()