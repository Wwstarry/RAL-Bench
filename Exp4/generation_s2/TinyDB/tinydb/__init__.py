"""
A tiny, file-based JSON "database" for local task management.

Public API:
- TinyDB: database wrapper
- where: query builder helper
- Query: query object
- Document: dict subclass carrying a doc_id
- JSONStorage: file storage backend
"""

from .database import TinyDB
from .queries import Query, where
from .table import Document
from .storages import JSONStorage

__all__ = ["TinyDB", "Query", "where", "Document", "JSONStorage"]