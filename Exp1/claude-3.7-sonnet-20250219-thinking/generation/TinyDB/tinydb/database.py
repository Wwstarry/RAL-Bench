import os
from typing import Dict, Optional, Any, Union, List
from .table import Table
from .storages import JSONStorage

class TinyDB:
    """
    The main database class for TinyDB.
    
    It provides access to tables and handles database operations.
    """
    
    def __init__(self, path: str = None, storage_cls=JSONStorage, **storage_kwargs):
        """
        Initialize a TinyDB instance.
        
        Args:
            path: Path to the database file.
            storage_cls: The storage class to use.
            **storage_kwargs: Additional arguments for the storage class.
        """
        self._storage = storage_cls(path, **storage_kwargs)
        self._tables = {}
        
    def table(self, name: str) -> Table:
        """
        Get access to a table.
        
        Creates the table if it doesn't exist.
        
        Args:
            name: The name of the table.
            
        Returns:
            The table instance.
        """
        if name not in self._tables:
            self._tables[name] = Table(name, self._storage)
        
        return self._tables[name]
    
    def tables(self) -> List[str]:
        """
        Get a list of all tables in the database.
        
        Returns:
            A list of table names.
        """
        data = self._storage.read()
        return list(data.keys())
    
    def purge_table(self, name: str) -> None:
        """
        Purge a table from the database.
        
        Args:
            name: The name of the table.
        """
        if name in self._tables:
            del self._tables[name]
        
        data = self._storage.read()
        if name in data:
            del data[name]
            self._storage.write(data)
    
    def purge_tables(self) -> None:
        """
        Purge all tables from the database.
        """
        self._tables.clear()
        self._storage.write({})
    
    def close(self) -> None:
        """
        Close the database.
        """
        self._storage.close()