from .storages import JSONStorage
from .table import Table

class TinyDB:
    """
    The main class for the database.

    This class provides a simple interface to a file-based, document-oriented
    database. It manages tables and storage.

    Usage:
        db = TinyDB('db.json')
        table = db.table('my_table')
        table.insert({'key': 'value'})
    """
    def __init__(self, path, storage=JSONStorage, **kwargs):
        """
        Create a new instance of TinyDB.

        :param path: The path to the database file.
        :param storage: The storage class to use. Defaults to JSONStorage.
        :param kwargs: Arguments passed to the storage class (e.g., indent=4).
        """
        self._storage = storage(path, **kwargs)
        self._tables = {}
        self.default_table_name = '_default'

    def table(self, name=None, **kwargs):
        """
        Get a table by name. If it doesn't exist, it will be created.

        :param name: The name of the table. Defaults to '_default'.
        :return: A Table instance.
        """
        name = name or self.default_table_name
        if name in self._tables:
            return self._tables[name]

        table = Table(self._storage, name)
        self._tables[name] = table
        return table

    def tables(self):
        """
        Get a set of all table names in the database.

        :return: A set of strings, where each string is a table name.
        """
        data = self._storage.read() or {}
        return set(data.keys())

    def close(self):
        """
        Close the database connection.
        This will close the underlying storage.
        """
        self._storage.close()

    def __enter__(self):
        """
        Enter the context manager.
        """
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit the context manager and close the database.
        """
        self.close()

    def __getattr__(self, name):
        """
        Get a table by attribute access.

        e.g., `db.my_table` is equivalent to `db.table('my_table')`
        """
        return self.table(name)

    def __repr__(self):
        return f'<{type(self).__name__} tables={list(self.tables())}, storage={self._storage}>'