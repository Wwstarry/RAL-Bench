# Lightweight dataset-like API in pure Python using sqlite3.

from .database import Database
from .table import Table

def connect(url: str) -> Database:
    """
    Connect to a database identified by a URL.

    Currently supports only SQLite URLs:
    - sqlite:///:memory:      -> in-memory database
    - sqlite:///path/to/file  -> file-based database
    - sqlite://relative/path  -> file-based (relative) database
    """
    return Database(url)

__all__ = ["connect", "Database", "Table"]