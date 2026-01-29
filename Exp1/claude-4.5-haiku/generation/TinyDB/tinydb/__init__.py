"""
TinyDB - A lightweight local task manager backed by JSON.
"""

from tinydb.database import TinyDB
from tinydb.table import Table
from tinydb.queries import Query

__version__ = "1.0.0"
__all__ = ["TinyDB", "Table", "Query"]