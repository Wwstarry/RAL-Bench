"""
Lightweight, pure-Python subset of the `dataset` library API, backed by sqlite3.

Only core functionality used by the test suite is implemented.
"""

from .database import Database, connect
from .table import Table

__all__ = ["connect", "Database", "Table"]