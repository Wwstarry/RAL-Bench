from dataset.database import Database

def connect(url, **kwargs):
    """
    Opens a new connection to a database.
    
    Args:
        url (str): The database URL (e.g., 'sqlite:///:memory:').
        **kwargs: Additional arguments passed to the database adapter.
        
    Returns:
        Database: The database object.
    """
    return Database(url, **kwargs)