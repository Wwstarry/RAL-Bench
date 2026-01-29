"""
TinyDB is a lightweight document oriented database.
"""
__version__ = '1.0.0'

from .database import TinyDB
from .queries import Query
from .storages import JSONStorage

__all__ = ('TinyDB', 'Query', 'JSONStorage')