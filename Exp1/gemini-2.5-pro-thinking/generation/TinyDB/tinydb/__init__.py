"""
TinyDB is a tiny, document oriented database optimized for your happiness.
"""
__version__ = '1.0.0'

from .database import TinyDB
from .queries import Query, where
from .storages import Storage, JSONStorage

__all__ = ('TinyDB', 'Storage', 'JSONStorage', 'Query', 'where')