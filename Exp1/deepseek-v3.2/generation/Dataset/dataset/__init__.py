"""
Lightweight tabular data access layer.
"""

__version__ = "1.0.0"
__all__ = ["connect", "Database", "Table"]

from dataset.database import Database
from dataset.table import Table


def connect(url: str) -> Database:
    """
    Connect to a database specified by the given URL.
    
    Args:
        url: Database connection URL (e.g., "sqlite:///:memory:")
        
    Returns:
        Database instance
    """
    return Database(url)