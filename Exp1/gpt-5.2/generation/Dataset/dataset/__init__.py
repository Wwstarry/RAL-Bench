"""
Lightweight, pure-Python tabular data access layer with a subset of the
`dataset` project's API.

Public API:
    - connect(url) -> Database
    - Database, Table
"""
from __future__ import annotations

from .database import Database


def connect(url: str, **kwargs) -> Database:
    """Connect to a database.

    Supported:
        - sqlite:///:memory:
        - sqlite:////absolute/path.db
        - sqlite:///relative/path.db
        - sqlite://relative/path.db  (treated as relative)

    Extra kwargs are accepted for compatibility and ignored.
    """
    return Database(url, **kwargs)


__all__ = ["connect", "Database"]