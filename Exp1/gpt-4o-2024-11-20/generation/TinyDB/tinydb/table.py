from .queries import Query

class Table:
    def __init__(self, name, records, storage):
        self._name = name
        self._records = records
        self._storage = storage

    def insert(self, record):
        self._records.append(record)
        self._save()

    def update(self, query, updates):
        for record in self._records:
            if query.match(record):
                record.update(updates)
        self._save()

    def remove(self, query):
        self._records = [record for record in self._records if not query.match(record)]
        self._save()

    def search(self, query):
        return [record for record in self._records if query.match(record)]

    def all(self):
        return self._records

    def _save(self):
        self._storage.update_table(self._name, self._records)