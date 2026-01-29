class Table:
    """
    Represents a collection of documents (tasks, projects, etc.).
    """
    def __init__(self, storage, name):
        self._storage = storage
        self._name = name

    def _read_table(self):
        """Helper to read the full DB and extract this table's data."""
        data = self._storage.read()
        return data.get(self._name, {})

    def _write_table(self, table_data):
        """Helper to write this table's data back to the DB."""
        data = self._storage.read()
        data[self._name] = table_data
        self._storage.write(data)

    def _get_next_id(self, table_data):
        """Simple auto-increment logic."""
        if not table_data:
            return 1
        # Keys are stored as strings in JSON, convert to int for max calculation
        ids = [int(k) for k in table_data.keys()]
        return max(ids) + 1

    def insert(self, document):
        """
        Insert a new document into the table.
        :param document: Dictionary representing the data.
        :return: The new document ID.
        """
        if not isinstance(document, dict):
            raise ValueError("Document must be a dictionary")

        data = self._read_table()
        doc_id = self._get_next_id(data)
        
        # Store ID within the document for convenience, but key by ID in storage
        document['_id'] = doc_id
        data[str(doc_id)] = document
        
        self._write_table(data)
        return doc_id

    def all(self):
        """
        Return all documents in the table.
        """
        data = self._read_table()
        return list(data.values())

    def get(self, doc_id):
        """
        Get a document by its ID.
        """
        data = self._read_table()
        return data.get(str(doc_id))

    def search(self, query):
        """
        Find documents matching a query.
        :param query: A Query object or a callable returning True/False.
        """
        data = self._read_table()
        results = []
        for doc in data.values():
            if query(doc):
                results.append(doc)
        return results

    def update(self, fields, query=None):
        """
        Update documents.
        :param fields: Dictionary of fields to update.
        :param query: Query object. If None, updates all documents.
        :return: List of updated document IDs.
        """
        data = self._read_table()
        updated_ids = []

        for doc_id, doc in data.items():
            # If no query is provided, update all. Otherwise check query.
            if query is None or query(doc):
                doc.update(fields)
                updated_ids.append(int(doc_id))
        
        if updated_ids:
            self._write_table(data)
        
        return updated_ids

    def remove(self, query=None):
        """
        Remove documents.
        :param query: Query object. If None, truncates the table.
        :return: List of removed document IDs.
        """
        data = self._read_table()
        
        if query is None:
            # Truncate
            self._write_table({})
            return []

        ids_to_remove = []
        for doc_id, doc in data.items():
            if query(doc):
                ids_to_remove.append(doc_id)
        
        for doc_id in ids_to_remove:
            del data[doc_id]
            
        if ids_to_remove:
            self._write_table(data)
            
        return [int(i) for i in ids_to_remove]

    def count(self, query):
        """
        Count documents matching the query.
        """
        return len(self.search(query))