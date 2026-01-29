class Table:
    """
    Represents a table in the database.
    """
    def __init__(self, storage, name):
        self._storage = storage
        self._name = name
        self._next_id = 1
        self._data = {}  # In-memory cache of table data {doc_id: doc}

        self._read_from_storage()

    def _read_from_storage(self):
        """
        Reads the table data from the storage.
        """
        raw_data = self._storage.read()
        if raw_data and self._name in raw_data:
            table_data = raw_data[self._name]
            self._data = {int(k): v for k, v in table_data.items()}
            if self._data:
                self._next_id = max(self._data.keys()) + 1
            else:
                self._next_id = 1
        else:
            self._data = {}
            self._next_id = 1

    def _write_to_storage(self):
        """
        Writes the entire database to storage.
        """
        data = self._storage.read() or {}
        # JSON keys must be strings
        data[self._name] = {str(k): v for k, v in self._data.items()}
        self._storage.write(data)

    def _get_doc_with_id(self, doc_id):
        """Helper to get a document and inject its ID."""
        if doc_id in self._data:
            doc = self._data[doc_id].copy()
            doc['doc_id'] = doc_id
            return doc
        return None

    def insert(self, document):
        """
        Insert a new document into the table.
        
        :param document: a dictionary
        :return: the inserted document's ID
        """
        if not isinstance(document, dict):
            raise ValueError("Document must be a dictionary")
        
        doc_id = self._next_id
        self._data[doc_id] = document.copy()
        self._next_id += 1
        self._write_to_storage()
        return doc_id

    def insert_multiple(self, documents):
        """
        Insert multiple documents into the table.
        
        :param documents: a list of dictionaries
        :return: a list of the inserted documents' IDs
        """
        doc_ids = []
        for doc in documents:
            if not isinstance(doc, dict):
                raise ValueError("Documents must be dictionaries")
            doc_id = self._next_id
            self._data[doc_id] = doc.copy()
            self._next_id += 1
            doc_ids.append(doc_id)
        
        if doc_ids:
            self._write_to_storage()
        return doc_ids

    def all(self):
        """
        Get all documents in the table.
        
        :return: a list of all documents
        """
        return [self._get_doc_with_id(doc_id) for doc_id in sorted(self._data.keys())]

    def search(self, query):
        """
        Search for all documents matching a query.
        
        :param query: a Query object
        :return: a list of matching documents
        """
        if not callable(query):
            raise ValueError("Query must be a callable object")
        
        return [doc for doc in self.all() if query(doc)]

    def get(self, query=None, doc_id=None):
        """
        Get exactly one document matching a query or a document ID.
        
        :param query: a Query object
        :param doc_id: an integer
        :return: the document or None
        """
        if doc_id is not None:
            return self._get_doc_with_id(doc_id)

        if query is not None:
            for doc_id in sorted(self._data.keys()):
                doc = self._get_doc_with_id(doc_id)
                if query(doc):
                    return doc
        
        return None

    def update(self, fields, query=None, doc_ids=None):
        """
        Update all documents matching a query or a list of document IDs.
        
        :param fields: a dictionary with fields to update
        :param query: a Query object
        :param doc_ids: a list of document IDs
        :return: a list of updated document IDs
        """
        if not isinstance(fields, dict):
            raise ValueError("Fields must be a dictionary")

        if doc_ids:
            target_ids = doc_ids
        elif query:
            target_ids = [doc['doc_id'] for doc in self.search(query)]
        else:
            return []

        updated_ids = []
        for doc_id in target_ids:
            if doc_id in self._data:
                self._data[doc_id].update(fields)
                updated_ids.append(doc_id)
        
        if updated_ids:
            self._write_to_storage()
            
        return updated_ids

    def remove(self, query=None, doc_ids=None):
        """
        Remove documents from the table.
        
        :param query: a Query object
        :param doc_ids: a list of document IDs
        :return: a list of removed document IDs
        """
        removed_ids = []
        if doc_ids:
            target_ids = doc_ids
        elif query:
            target_ids = [doc['doc_id'] for doc in self.search(query)]
        else:
            return []

        for doc_id in target_ids:
            if doc_id in self._data:
                del self._data[doc_id]
                removed_ids.append(doc_id)
        
        if removed_ids:
            self._write_to_storage()
            
        return removed_ids

    def truncate(self):
        """
        Remove all documents from the table.
        """
        self._data.clear()
        self._next_id = 1
        self._write_to_storage()

    def count(self, query):
        """
        Count the documents matching a query.
        
        :param query: a Query object
        :return: the number of matching documents
        """
        return len(self.search(query))

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self.all())