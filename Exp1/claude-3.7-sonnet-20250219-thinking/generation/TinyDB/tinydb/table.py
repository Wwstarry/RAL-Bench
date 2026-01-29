from typing import Dict, List, Any, Callable, Optional, Union
from .queries import Query

class Table:
    """
    A table in the database.
    
    It provides methods to insert, update, and query documents.
    """
    
    def __init__(self, name: str, storage):
        """
        Initialize a table instance.
        
        Args:
            name: The name of the table.
            storage: The storage instance to use.
        """
        self.name = name
        self._storage = storage
    
    def _get_data(self) -> List[Dict]:
        """
        Get the data stored in this table.
        
        Returns:
            A list of documents.
        """
        data = self._storage.read()
        if self.name not in data:
            data[self.name] = []
            self._storage.write(data)
        
        return data[self.name]
    
    def _set_data(self, data: List[Dict]) -> None:
        """
        Write data to this table.
        
        Args:
            data: The data to write.
        """
        all_data = self._storage.read()
        all_data[self.name] = data
        self._storage.write(all_data)
    
    def all(self) -> List[Dict]:
        """
        Get all documents in the table.
        
        Returns:
            A list of all documents.
        """
        return self._get_data()
    
    def insert(self, document: Dict) -> int:
        """
        Insert a document into the table.
        
        Args:
            document: The document to insert.
            
        Returns:
            The ID of the inserted document.
        """
        data = self._get_data()
        
        # Generate a document ID
        doc_id = len(data)
        document['id'] = doc_id
        
        data.append(document)
        self._set_data(data)
        
        return doc_id
    
    def insert_multiple(self, documents: List[Dict]) -> List[int]:
        """
        Insert multiple documents into the table.
        
        Args:
            documents: The documents to insert.
            
        Returns:
            A list of document IDs.
        """
        data = self._get_data()
        doc_ids = []
        
        for document in documents:
            doc_id = len(data)
            document['id'] = doc_id
            data.append(document)
            doc_ids.append(doc_id)
        
        self._set_data(data)
        
        return doc_ids
    
    def search(self, query) -> List[Dict]:
        """
        Search for documents that match the query.
        
        Args:
            query: The query to search with.
            
        Returns:
            A list of matching documents.
        """
        data = self._get_data()
        return [doc for doc in data if query(doc)]
    
    def get(self, query) -> Optional[Dict]:
        """
        Get a single document that matches the query.
        
        Args:
            query: The query to search with.
            
        Returns:
            The matching document or None.
        """
        results = self.search(query)
        return results[0] if results else None
    
    def update(self, fields: Dict, query) -> List[int]:
        """
        Update documents that match the query.
        
        Args:
            fields: The fields to update.
            query: The query to match documents.
            
        Returns:
            A list of updated document IDs.
        """
        data = self._get_data()
        updated = []
        
        for i, doc in enumerate(data):
            if query(doc):
                data[i].update(fields)
                updated.append(doc['id'])
        
        self._set_data(data)
        
        return updated
    
    def remove(self, query) -> List[int]:
        """
        Remove documents that match the query.
        
        Args:
            query: The query to match documents.
            
        Returns:
            A list of removed document IDs.
        """
        data = self._get_data()
        removed = []
        
        data_new = []
        for doc in data:
            if query(doc):
                removed.append(doc['id'])
            else:
                data_new.append(doc)
        
        self._set_data(data_new)
        
        return removed
    
    def count(self, query=None) -> int:
        """
        Count documents that match the query.
        
        Args:
            query: The query to match documents.
            
        Returns:
            The number of matching documents.
        """
        if query is None:
            return len(self._get_data())
        else:
            return len(self.search(query))