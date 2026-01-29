"""
dataset - A lightweight tabular data access layer for Python
"""

from dataset.database import Database
from dataset.table import Table


def connect(url):
    """
    Connect to a database and return a Database instance.
    
    Args:
        url: Database URL (e.g., "sqlite:///:memory:")
    
    Returns:
        Database instance
    """
    return Database(url)


__all__ = ['connect', 'Database', 'Table']