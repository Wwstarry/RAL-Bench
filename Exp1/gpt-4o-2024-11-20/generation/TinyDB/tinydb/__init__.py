# This is the entry point for the tinydb package.
# It imports and exposes the main components of the system.

from .database import TinyDB
from .queries import Query
from .storages import JSONStorage

__all__ = ['TinyDB', 'Query', 'JSONStorage']