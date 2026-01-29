import os
from .table import Table
from .storages import JSONStorage

class TinyDB:
    def __init__(self, storage_path):
        self.storage = JSONStorage(storage_path)
        self.tables = {}
        self._load_tables()

    def _load_tables(self):
        data = self.storage.read()
        if not data:
            return
            
        for table_name, docs in data.items():
            table = Table(table_name, self.storage)
            table._documents = {int(doc_id): doc for doc_id, doc in docs.items()}
            self.tables[table_name] = table

    def table(self, name):
        if name not in self.tables:
            self.tables[name] = Table(name, self.storage)
        return self.tables[name]

    def close(self):
        self.storage.close()