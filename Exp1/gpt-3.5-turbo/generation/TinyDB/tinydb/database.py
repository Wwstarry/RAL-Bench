import os
from threading import RLock

from .storages import JSONStorage
from .table import Table


class TinyDB:
    def __init__(self, storage=None, path=None, default_table="tasks"):
        """
        Initialize the TinyDB instance.

        :param storage: Storage instance to use. If None, JSONStorage with path is used.
        :param path: Path to the JSON file if storage is None.
        :param default_table: Name of the default table.
        """
        if storage is None:
            if path is None:
                raise ValueError("Either storage or path must be provided")
            storage = JSONStorage(path)
        self._storage = storage
        self._lock = RLock()
        self._tables = {}
        self._default_table_name = default_table
        self._read()

    def _read(self):
        with self._lock:
            self._data = self._storage.read() or {}
            # Ensure default table exists
            if self._default_table_name not in self._data:
                self._data[self._default_table_name] = []
            # Initialize Table instances
            for table_name, records in self._data.items():
                self._tables[table_name] = Table(table_name, self)

    def _write(self):
        with self._lock:
            self._storage.write(self._data)

    def table(self, name=None):
        """
        Get a Table instance by name.

        :param name: Table name. If None, returns default table.
        :return: Table instance.
        """
        if name is None:
            name = self._default_table_name
        with self._lock:
            if name not in self._tables:
                self._data.setdefault(name, [])
                self._tables[name] = Table(name, self)
            return self._tables[name]

    def all_tables(self):
        """
        Return list of all table names.

        :return: list of table names
        """
        with self._lock:
            return list(self._data.keys())

    def close(self):
        """
        Close the database and write all changes.
        """
        with self._lock:
            self._write()

    def _get_table_data(self, table_name):
        with self._lock:
            return self._data.setdefault(table_name, [])

    def _set_table_data(self, table_name, data):
        with self._lock:
            self._data[table_name] = data
            self._write()