import copy

class Document(dict):
    """
    A document stored in the database.
    It's a subclass of dict, with an additional `doc_id` attribute.
    """
    def __init__(self, value, doc_id):
        super().__init__(value)
        self.doc_id = doc_id

class Table:
    """
    Represents a table in the database, which is a collection of documents.
    """
    def __init__(self, storage, name):
        self._storage = storage
        self._name = name
        self._last_id = 0

    def _read_data(self):
        """
        Read all data for this table from the storage.
        """
        data = self._storage.read()
        if data is None or self._name not in data:
            self._last_id = 0
            return {}

        table_data = data[self._name]
        self._last_id = table_data.get('_last_id', 0)
        return {int(k): v for k, v in table_data.items() if k != '_last_id'}

    def _write_data(self, data):
        """
        Write the data for this table to the storage.
        """
        full_data = self._storage.read() or {}
        full_data[self._name] = {'_last_id': self._last_id, **{str(k): v for k, v in data.items()}}
        self._storage.write(full_data)

    def insert(self, document):
        """
        Insert a new document into the table.

        :param document: A dictionary representing the document.
        :return: The ID of the inserted document.
        """
        if not isinstance(document, dict):
            raise ValueError("Document must be a dictionary")

        data = self._read_data()
        self._last_id += 1
        doc_id = self._last_id

        data[doc_id] = copy.deepcopy(document)
        self._write_data(data)
        return doc_id

    def insert_multiple(self, documents):
        """
        Insert multiple documents into the table.

        :param documents: A list of dictionaries.
        :return: A list of IDs of the inserted documents.
        """
        if not all(isinstance(doc, dict) for doc in documents):
            raise ValueError("All documents must be dictionaries")

        data = self._read_data()
        doc_ids = []

        for doc in documents:
            self._last_id += 1
            doc_id = self._last_id
            data[doc_id] = copy.deepcopy(doc)
            doc_ids.append(doc_id)

        self._write_data(data)
        return doc_ids

    def all(self):
        """
        Get all documents from the table.

        :return: A list of Document objects.
        """
        data = self._read_data()
        return [Document(doc, doc_id) for doc_id, doc in data.items()]

    def search(self, query):
        """
        Search for documents matching a query.

        :param query: A query object.
        :return: A list of matching Document objects.
        """
        if not callable(query):
            raise ValueError("Query must be a callable object")

        return [doc for doc in self.all() if query(doc)]

    def get(self, query=None, doc_id=None):
        """
        Get a single document by query or doc_id.

        :param query: A query object.
        :param doc_id: The ID of the document.
        :return: A single Document object or None.
        """
        if doc_id is not None:
            data = self._read_data()
            doc = data.get(int(doc_id))
            return Document(doc, doc_id) if doc else None

        if query is not None:
            for doc in self.all():
                if query(doc):
                    return doc
        return None

    def update(self, fields, query=None, doc_ids=None):
        """
        Update documents in the table.

        :param fields: A dictionary of fields to update.
        :param query: A query to select documents to update.
        :param doc_ids: A list of document IDs to update.
        :return: A list of updated document IDs.
        """
        if not isinstance(fields, dict):
            raise ValueError("Fields to update must be a dictionary")

        data = self._read_data()
        updated_ids = []

        if doc_ids:
            target_ids = [int(i) for i in doc_ids]
        elif query:
            target_ids = [doc.doc_id for doc in self.search(query)]
        else:
            # Update all documents if neither query nor doc_ids is provided
            target_ids = list(data.keys())

        for doc_id in target_ids:
            if doc_id in data:
                data[doc_id].update(fields)
                updated_ids.append(doc_id)

        if updated_ids:
            self._write_data(data)

        return updated_ids

    def remove(self, query=None, doc_ids=None):
        """
        Remove documents from the table.

        :param query: A query to select documents to remove.
        :param doc_ids: A list of document IDs to remove.
        :return: A list of removed document IDs.
        """
        data = self._read_data()
        removed_ids = []

        if doc_ids:
            target_ids = [int(i) for i in doc_ids]
        elif query:
            target_ids = [doc.doc_id for doc in self.search(query)]
        else:
            # For safety, do not remove all documents unless explicitly told to
            return []

        for doc_id in target_ids:
            if doc_id in data:
                del data[doc_id]
                removed_ids.append(doc_id)

        if removed_ids:
            self._write_data(data)

        return removed_ids

    def count(self, query):
        """
        Count the number of documents matching a query.

        :param query: A query object.
        :return: The number of matching documents.
        """
        return len(self.search(query))

    def truncate(self):
        """
        Remove all documents from the table.
        """
        self._write_data({})
        self._last_id = 0

    def __len__(self):
        return len(self._read_data())