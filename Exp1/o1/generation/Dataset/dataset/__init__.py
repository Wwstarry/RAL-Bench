import sqlite3
from .database import Database

def connect(url):
    """
    Connect to the given database URL and return a Database instance.
    Currently only supports URLs of the form 'sqlite:///...'.
    """
    if not url.startswith('sqlite://'):
        raise ValueError("Only sqlite URLs are supported in this implementation.")

    # Handle special case for in-memory
    if url == 'sqlite:///:memory:':
        path = ':memory:'
    else:
        # Strip sqlite:///
        path = url.replace('sqlite:///', '', 1)

    conn = sqlite3.connect(path, isolation_level=None)  # autocommit mode
    conn.row_factory = sqlite3.Row
    return Database(conn)