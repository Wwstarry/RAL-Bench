# dataset/__init__.py
from .database import Database

__version__ = '0.1.0'

def connect(url, **kwargs):
    """Connect to a database using the specified URL.
    
    Args:
        url (str): Database connection URL
        **kwargs: Additional parameters to pass to the database
        
    Returns:
        Database: A database connection object
    """
    return Database(url, **kwargs)