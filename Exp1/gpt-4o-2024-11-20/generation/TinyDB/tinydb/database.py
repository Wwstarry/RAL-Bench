import os
from .table import Table
from .storages import JSONStorage

class TinyDB:
    def __init__(self, path, storage=JSONStorage):
        self._path = path
        self._storage = storage(path)
        self._tables = {}
        self._load_tables()

    def _load_tables(self):
        data = self._storage.read()
        if data:
            for table_name, records in data.items():
                self._tables[table_name] = Table(table_name, records, self._storage)

    def table(self, name):
        if name not in self._tables:
            self._tables[name] = Table(name, [], self._storage)
        return self._tables[name]

    def all_tables(self):
        return list(self._tables.keys())

    def save(self):
        data = {name: table.all() for name, table in self._tables.items()}
        self._storage.write(data)

    def close(self):
        self.save()
        self._storage.close()