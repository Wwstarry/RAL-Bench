import time
from .queries import Query

class Table:
    def __init__(self, name, storage):
        self.name = name
        self.storage = storage
        self._documents = {}
        self._next_id = 1

    def _save(self):
        all_data = self.storage.read() or {}
        all_data[self.name] = self._documents
        self.storage.write(all_data)

    def insert(self, document):
        timestamp = time.time()
        document['created_at'] = timestamp
        document['updated_at'] = timestamp
        
        doc_id = self._next_id
        self._documents[doc_id] = document
        self._next_id += 1
        self._save()
        return doc_id

    def update(self, updates, cond=None):
        updated_ids = []
        for doc_id, doc in self._documents.items():
            if cond is None or cond(doc):
                updates['updated_at'] = time.time()
                doc.update(updates)
                updated_ids.append(doc_id)
                
        if updated_ids:
            self._save()
        return updated_ids

    def remove(self, cond=None):
        to_remove = [doc_id for doc_id, doc in self._documents.items() 
                     if cond is None or cond(doc)]
        for doc_id in to_remove:
            del self._documents[doc_id]
            
        if to_remove:
            self._save()
        return len(to_remove)

    def search(self, cond=None):
        return [doc for doc in self._documents.values() 
                if cond is None or cond(doc)]

    def count(self, cond=None):
        return len(self.search(cond))

    def get(self, doc_id):
        return self._documents.get(doc_id)

    def all(self):
        return list(self._documents.values())