# dataset/__init__.py

from .database import Database, connect
from .table import Table

__all__ = ['Database', 'Table', 'connect']