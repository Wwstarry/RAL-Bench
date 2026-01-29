"""
TinyDB - A lightweight local task manager backed by JSON storage.
"""
from .database import TinyDB
from .table import Table
from .queries import Query
from .storages import JSONStorage

__version__ = "1.0.0"
__all__ = ["TinyDB", "Table", "Query", "JSONStorage"]