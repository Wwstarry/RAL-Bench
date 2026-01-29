"""
Database implementation for TinyDB
"""

import os
from typing import Dict, List, Optional, Any, Callable
from .table import Table
from .storages import JSONStorage, Storage


class TinyDB:
    """
    Main database class that manages tables and storage
    """
    
    def __init__(self, path: Optional[str] = None, storage: Optional[Storage] = None):
        """
        Initialize the database
        
        Args:
            path: Path to the database file (if using JSONStorage)
            storage: Custom storage backend (defaults to JSONStorage)
        """
        if storage is None:
            if path is None:
                raise ValueError("Either path or storage must be provided")
            storage = JSONStorage(path)
        
        self._storage = storage
        self._tables: Dict[str, Table] = {}
        self._default_table_name = '_default'
        
    def table(self, name: str = None) -> Table:
        """
        Get or create a table
        
        Args:
            name: Name of the table (defaults to '_default')
            
        Returns:
            Table instance
        """
        if name is None:
            name = self._default_table_name
            
        if name not in self._tables:
            self._tables[name] = Table(name, self._storage)
            
        return self._tables[name]
    
    def tables(self) -> List[str]:
        """
        Get list of all table names
        
        Returns:
            List of table names
        """
        data = self._storage.read()
        return list(data.keys()) if data else []
    
    def drop_table(self, name: str):
        """
        Drop a table from the database
        
        Args:
            name: Name of the table to drop
        """
        if name in self._tables:
            del self._tables[name]
        
        data = self._storage.read()
        if name in data:
            del data[name]
            self._storage.write(data)
    
    def drop_tables(self):
        """
        Drop all tables from the database
        """
        self._tables.clear()
        self._storage.write({})
    
    def close(self):
        """
        Close the database and flush any pending writes
        """
        self._tables.clear()
    
    # Convenience methods that delegate to default table
    def insert(self, document: Dict[str, Any]) -> int:
        """Insert a document into the default table"""
        return self.table().insert(document)
    
    def insert_multiple(self, documents: List[Dict[str, Any]]) -> List[int]:
        """Insert multiple documents into the default table"""
        return self.table().insert_multiple(documents)
    
    def all(self) -> List[Dict[str, Any]]:
        """Get all documents from the default table"""
        return self.table().all()
    
    def search(self, cond: Callable) -> List[Dict[str, Any]]:
        """Search documents in the default table"""
        return self.table().search(cond)
    
    def get(self, cond: Callable) -> Optional[Dict[str, Any]]:
        """Get a single document from the default table"""
        return self.table().get(cond)
    
    def update(self, fields: Dict[str, Any], cond: Callable) -> List[int]:
        """Update documents in the default table"""
        return self.table().update(fields, cond)
    
    def remove(self, cond: Callable) -> List[int]:
        """Remove documents from the default table"""
        return self.table().remove(cond)
    
    def truncate(self):
        """Remove all documents from the default table"""
        return self.table().truncate()
    
    def count(self, cond: Callable = None) -> int:
        """Count documents in the default table"""
        return self.table().count(cond)