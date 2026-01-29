"""
Table module for managing collections of documents.
"""

from typing import Dict, Any, List, Optional, Callable
from tinydb.storages import JSONStorage


class Table:
    """
    Represents a table (collection) in the database.
    """

    def __init__(self, name: str, storage: JSONStorage):
        """
        Initialize a table.

        Args:
            name: Name of the table
            storage: Storage backend instance
        """
        self.name = name
        self.storage = storage
        self._ensure_table_exists()

    def _ensure_table_exists(self) -> None:
        """Ensure the table exists in storage."""
        data = self.storage.read()
        if self.name not in data:
            data[self.name] = []
            self.storage.write(data)

    def _get_next_id(self) -> int:
        """Get the next available document ID."""
        data = self.storage.read()
        docs = data.get(self.name, [])
        if not docs:
            return 1
        return max(doc.get("id", 0) for doc in docs) + 1

    def insert(self, document: Dict[str, Any]) -> int:
        """
        Insert a document into the table.

        Args:
            document: Document to insert

        Returns:
            ID of the inserted document
        """
        data = self.storage.read()
        doc_id = self._get_next_id()
        document["id"] = doc_id
        data[self.name].append(document)
        self.storage.write(data)
        return doc_id

    def insert_multiple(self, documents: List[Dict[str, Any]]) -> List[int]:
        """
        Insert multiple documents into the table.

        Args:
            documents: List of documents to insert

        Returns:
            List of inserted document IDs
        """
        ids = []
        for doc in documents:
            ids.append(self.insert(doc))
        return ids

    def all(self) -> List[Dict[str, Any]]:
        """
        Get all documents from the table.

        Returns:
            List of all documents
        """
        data = self.storage.read()
        return data.get(self.name, [])

    def get(self, doc_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            Document or None if not found
        """
        data = self.storage.read()
        docs = data.get(self.name, [])
        for doc in docs:
            if doc.get("id") == doc_id:
                return doc
        return None

    def update(self, doc_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update a document by ID.

        Args:
            doc_id: Document ID
            updates: Dictionary of fields to update

        Returns:
            True if document was updated, False otherwise
        """
        data = self.storage.read()
        docs = data.get(self.name, [])
        for doc in docs:
            if doc.get("id") == doc_id:
                doc.update(updates)
                self.storage.write(data)
                return True
        return False

    def remove(self, doc_id: int) -> bool:
        """
        Remove a document by ID.

        Args:
            doc_id: Document ID

        Returns:
            True if document was removed, False otherwise
        """
        data = self.storage.read()
        docs = data.get(self.name, [])
        for i, doc in enumerate(docs):
            if doc.get("id") == doc_id:
                docs.pop(i)
                self.storage.write(data)
                return True
        return False

    def search(self, condition: Callable[[Dict[str, Any]], bool]) -> List[Dict[str, Any]]:
        """
        Search for documents matching a condition.

        Args:
            condition: Callable that returns True for matching documents

        Returns:
            List of matching documents
        """
        data = self.storage.read()
        docs = data.get(self.name, [])
        return [doc for doc in docs if condition(doc)]

    def count(self) -> int:
        """
        Count total documents in the table.

        Returns:
            Number of documents
        """
        data = self.storage.read()
        return len(data.get(self.name, []))

    def truncate(self) -> None:
        """Remove all documents from the table."""
        data = self.storage.read()
        data[self.name] = []
        self.storage.write(data)