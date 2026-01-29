"""
Lightweight, pure-Python subset of the `dataset` project API.

This implementation focuses on the core behaviors used by the test-suite:
- dataset.connect(url) -> Database
- Database: table access, transactions, and SQL querying
- Table: insert/update/upsert/delete and basic querying/introspection/index helpers

Supported URLs:
- sqlite:///:memory:
- sqlite:////absolute/path.db
- sqlite:///relative/path.db
- sqlite://relative/path.db
"""

from .database import Database, connect

__all__ = ["Database", "connect"]