"""
TinyDB - A lightweight document-oriented database
"""

from .database import TinyDB
from .queries import Query, where
from .table import Table
from .storages import JSONStorage, MemoryStorage

__version__ = '1.0.0'
__all__ = ['TinyDB', 'Query', 'where', 'Table', 'JSONStorage', 'MemoryStorage']