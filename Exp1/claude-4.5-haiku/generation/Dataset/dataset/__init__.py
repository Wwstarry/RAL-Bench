"""
dataset: A lightweight tabular data access layer for Python.
"""

from dataset.database import Database


def connect(url):
    """
    Create a connection to a database.
    
    Args:
        url: Database URL (e.g., 'sqlite:///:memory:' or 'sqlite:///path/to/db.db')
    
    Returns:
        A Database instance.
    """
    return Database(url)


__all__ = ['connect', 'Database']