"""
Table module for TinyDB.
"""
from typing import Dict, List, Optional, Any, Union, Callable
from .queries import Query


class Table:
    """Table class for storing documents."""
    
    def __init__(self, name: str, storage, initial_data: List[Dict] = None):
        """
        Initialize a table.
        
        Args:
            name: Table name
            storage: Storage instance
            initial_data: Initial data for the table
        """
        self.name = name
        self.storage = storage
        self._data: List[Dict] = initial_data or []
        self._last_id = len(self._data)
    
    def insert(self, document: Dict) -> int:
        """
        Insert a document.
        
        Args:
            document: Document to insert
            
        Returns:
            Document ID
        """
        doc_id = self._last_id + 1
        self._data.append({**document, "doc_id": doc_id})
        self._last_id = doc_id
        self._sync()
        return doc_id
    
    def insert_multiple(self, documents: List[Dict]) -> List[int]:
        """
        Insert multiple documents.
        
        Args:
            documents: List of documents to insert
            
        Returns:
            List of document IDs
        """
        doc_ids = []
        for doc in documents:
            doc_id = self.insert(doc)
            doc_ids.append(doc_id)
        return doc_ids
    
    def get(self, doc_id: int = None, cond: Callable = None) -> Optional[Dict]:
        """
        Get a document by ID or condition.
        
        Args:
            doc_id: Document ID
            cond: Condition function
            
        Returns:
            Document or None
        """
        if doc_id is not None:
            for doc in self._data:
                if doc.get("doc_id") == doc_id:
                    return doc
            return None
        
        if cond is not None:
            for doc in self._data:
                if cond(doc):
                    return doc
            return None
        
        return None
    
    def search(self, query: Query) -> List[Dict]:
        """
        Search documents matching query.
        
        Args:
            query: Query object
            
        Returns:
            List of matching documents
        """
        return [doc for doc in self._data if query(doc)]
    
    def update(self, fields: Dict, cond: Callable = None, doc_ids: List[int] = None) -> bool:
        """
        Update documents.
        
        Args:
            fields: Fields to update
            cond: Condition function
            doc_ids: List of document IDs
            
        Returns:
            True if any document was updated
        """
        updated = False
        
        for doc in self._data:
            if doc_ids is not None and doc.get("doc_id") not in doc_ids:
                continue
            
            if cond is not None and not cond(doc):
                continue
            
            doc.update(fields)
            updated = True
        
        if updated:
            self._sync()
        
        return updated
    
    def remove(self, cond: Callable = None, doc_ids: List[int] = None) -> bool:
        """
        Remove documents.
        
        Args:
            cond: Condition function
            doc_ids: List of document IDs
            
        Returns:
            True if any document was removed
        """
        to_remove = []
        
        for i, doc in enumerate(self._data):
            if doc_ids is not None and doc.get("doc_id") not in doc_ids:
                continue
            
            if cond is not None and not cond(doc):
                continue
            
            to_remove.append(i)
        
        for i in sorted(to_remove, reverse=True):
            del self._data[i]
        
        if to_remove:
            self._sync()
            return True
        
        return False
    
    def all(self) -> List[Dict]:
        """
        Get all documents.
        
        Returns:
            List of all documents
        """
        return self._data.copy()
    
    def count(self, query: Query = None) -> int:
        """
        Count documents.
        
        Args:
            query: Optional query
            
        Returns:
            Number of documents
        """
        if query is None:
            return len(self._data)
        return len(self.search(query))
    
    def _query_builder(self) -> Query:
        """
        Get a query builder.
        
        Returns:
            Query instance
        """
        return Query()
    
    def _get_all(self) -> List[Dict]:
        """
        Get all documents (internal use).
        
        Returns:
            List of all documents
        """
        return self._data
    
    def _sync(self) -> None:
        """Sync table data to storage."""
        self.storage._sync_table(self.name, self._data)