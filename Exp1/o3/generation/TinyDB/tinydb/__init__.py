"""
Light-weight embedded document database (tinydb like) – simplified.

The goal of this stripped-down re-implementation is to provide just enough
functionality to act as local JSON backed task store that supports:

    * Several named tables (e.g. "tasks", "projects")
    * CRUD operations (insert / get / search / update / remove)
    * Very small query DSL (==, !=, <, <=, >, >=, & (and), | (or), ~ (not))
    * File-based persistence (atomic write) + pure in-memory mode

Only the modules that are required by the assignment are provided.  Nothing
outside the standard library is used, so the package works on vanilla Python.
"""

from .database import TinyDB
from .queries import Query

__all__ = ["TinyDB", "Query"]