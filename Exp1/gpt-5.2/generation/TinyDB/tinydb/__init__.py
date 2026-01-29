"""
A tiny, file-based task manager "database" inspired by TinyDB.

This package provides:
- JSON file storage with atomic-ish writes
- Table abstraction with CRUD operations
- Query builder for filtering documents
- Lightweight analytics helpers
"""

from .database import Database
from .table import Table
from .queries import Query, where
from .storages import JSONStorage

__all__ = ["Database", "Table", "Query", "where", "JSONStorage"]