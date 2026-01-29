from .table import Table
from .storages import JSONStorage

class TinyDB:
    """
    The main database class.
    Acts as a manager for tables and holds the storage reference.
    """
    def __init__(self, path, storage=JSONStorage):
        """
        :param path: Path to the database file.
        :param storage: Storage class to use (default: JSONStorage).
        """
        self._storage = storage(path)
        self._tables = {}

    def table(self, name='_default'):
        """
        Get access to a specific table.
        """
        if name not in self._tables:
            self._tables[name] = Table(self._storage, name)
        return self._tables[name]

    def drop_table(self, name):
        """
        Remove a table from the database.
        """
        data = self._storage.read()
        if name in data:
            del data[name]
            self._storage.write(data)
        
        if name in self._tables:
            del self._tables[name]

    def close(self):
        """
        Close the storage (if applicable).
        """
        pass

    # Proxy methods to the default table for convenience
    def insert(self, document):
        return self.table().insert(document)

    def all(self):
        return self.table().all()

    def search(self, query):
        return self.table().search(query)

    def update(self, fields, query=None):
        return self.table().update(fields, query)

    def remove(self, query=None):
        return self.table().remove(query)