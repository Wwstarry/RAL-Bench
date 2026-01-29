from .storages import JSONStorage
from .table import Table

class TinyDB:
    """
    The main class for a TinyDB database.
    """
    DEFAULT_TABLE = '_default'
    DEFAULT_STORAGE = JSONStorage

    def __init__(self, *args, **kwargs):
        """
        Create a new instance of TinyDB.
        
        All arguments are passed to the storage constructor.
        
        :param storage: The storage class to use.
        """
        storage = kwargs.pop('storage', self.DEFAULT_STORAGE)
        self._storage = storage(*args, **kwargs)
        self._tables = {}

    def table(self, name=DEFAULT_TABLE, **kwargs):
        """
        Get a table by name. If it doesn't exist, it will be created.
        
        :param name: The name of the table.
        :return: an instance of Table
        """
        if name in self._tables:
            return self._tables[name]
        
        table = Table(self._storage, name)
        self._tables[name] = table
        return table

    def tables(self):
        """
        Get a set of all table names.
        
        :return: a set of strings
        """
        data = self._storage.read() or {}
        return set(data.keys())

    def close(self):
        """
        Close the database.
        """
        self._storage.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def __getattr__(self, name):
        """
        Get a table by attribute.
        """
        return self.table(name)

    def __len__(self):
        """
        Get the number of tables in the database.
        """
        return len(self.tables())