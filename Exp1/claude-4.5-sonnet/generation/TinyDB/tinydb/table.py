"""
Table implementation for TinyDB
"""

from typing import Dict, List, Optional, Any, Callable
from .storages import Storage


class Table:
    """
    Represents a table in the database
    """
    
    def __init__(self, name: str, storage: Storage):
        """
        Initialize a table
        
        Args:
            name: Name of the table
            storage: Storage backend
        """
        self._name = name
        self._storage = storage
        self._next_id = 1
        self._update_next_id()
    
    def _update_next_id(self):
        """Update the next available document ID"""
        data = self._read_table()
        if data:
            max_id = max(int(doc_id) for doc_id in data.keys())
            self._next_id = max_id + 1
        else:
            self._next_id = 1
    
    def _read_table(self) -> Dict[str, Dict[str, Any]]:
        """Read the table data from storage"""
        all_data = self._storage.read()
        return all_data.get(self._name, {})
    
    def _write_table(self, table_data: Dict[str, Dict[str, Any]]):
        """Write the table data to storage"""
        all_data = self._storage.read()
        all_data[self._name] = table_data
        self._storage.write(all_data)
    
    def insert(self, document: Dict[str, Any]) -> int:
        """
        Insert a document into the table
        
        Args:
            document: Document to insert
            
        Returns:
            Document ID
        """
        table_data = self._read_table()
        doc_id = self._next_id
        self._next_id += 1
        
        # Store document with its ID
        doc_with_id = document.copy()
        doc_with_id['_id'] = doc_id
        table_data[str(doc_id)] = doc_with_id
        
        self._write_table(table_data)
        return doc_id
    
    def insert_multiple(self, documents: List[Dict[str, Any]]) -> List[int]:
        """
        Insert multiple documents into the table
        
        Args:
            documents: List of documents to insert
            
        Returns:
            List of document IDs
        """
        table_data = self._read_table()
        doc_ids = []
        
        for document in documents:
            doc_id = self._next_id
            self._next_id += 1
            doc_ids.append(doc_id)
            
            doc_with_id = document.copy()
            doc_with_id['_id'] = doc_id
            table_data[str(doc_id)] = doc_with_id
        
        self._write_table(table_data)
        return doc_ids
    
    def all(self) -> List[Dict[str, Any]]:
        """
        Get all documents from the table
        
        Returns:
            List of all documents
        """
        table_data = self._read_table()
        return list(table_data.values())
    
    def search(self, cond: Callable) -> List[Dict[str, Any]]:
        """
        Search for documents matching a condition
        
        Args:
            cond: Condition function that takes a document and returns bool
            
        Returns:
            List of matching documents
        """
        table_data = self._read_table()
        results = []
        
        for doc in table_data.values():
            if cond(doc):
                results.append(doc)
        
        return results
    
    def get(self, cond: Callable) -> Optional[Dict[str, Any]]:
        """
        Get a single document matching a condition
        
        Args:
            cond: Condition function that takes a document and returns bool
            
        Returns:
            First matching document or None
        """
        table_data = self._read_table()
        
        for doc in table_data.values():
            if cond(doc):
                return doc
        
        return None
    
    def update(self, fields: Dict[str, Any], cond: Callable) -> List[int]:
        """
        Update documents matching a condition
        
        Args:
            fields: Fields to update
            cond: Condition function that takes a document and returns bool
            
        Returns:
            List of updated document IDs
        """
        table_data = self._read_table()
        updated_ids = []
        
        for doc_id, doc in table_data.items():
            if cond(doc):
                doc.update(fields)
                updated_ids.append(int(doc_id))
        
        if updated_ids:
            self._write_table(table_data)
        
        return updated_ids
    
    def remove(self, cond: Callable) -> List[int]:
        """
        Remove documents matching a condition
        
        Args:
            cond: Condition function that takes a document and returns bool
            
        Returns:
            List of removed document IDs
        """
        table_data = self._read_table()
        removed_ids = []
        
        for doc_id, doc in list(table_data.items()):
            if cond(doc):
                del table_data[doc_id]
                removed_ids.append(int(doc_id))
        
        if removed_ids:
            self._write_table(table_data)
        
        return removed_ids
    
    def truncate(self):
        """Remove all documents from the table"""
        self._write_table({})
        self._next_id = 1
    
    def count(self, cond: Callable = None) -> int:
        """
        Count documents in the table
        
        Args:
            cond: Optional condition function
            
        Returns:
            Number of matching documents
        """
        if cond is None:
            return len(self._read_table())
        else:
            return len(self.search(cond))