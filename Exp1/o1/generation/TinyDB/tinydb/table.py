from copy import deepcopy
from .queries import Query

class Table:
    """
    Represents a single table within the TinyDB-like database.
    Provides CRUD operations on documents.
    """

    def __init__(self, name, db_cache, storage):
        self.name = name
        self._db_cache = db_cache  # In-memory dictionary for the entire DB
        self._storage = storage
        if name not in self._db_cache:
            self._db_cache[name] = []
        self._ensure_doc_ids()

    def insert(self, document):
        """
        Insert a new document into the table. Automatically assigns a doc_id.
        Returns the generated doc_id.
        """
        new_doc = deepcopy(document)
        new_doc_id = self._generate_new_id()
        new_doc["_id"] = new_doc_id
        self._db_cache[self.name].append(new_doc)
        self._write()
        return new_doc_id

    def all(self):
        """
        Return all documents in the table.
        """
        return deepcopy(self._db_cache[self.name])

    def search(self, cond):
        """
        Search for documents that match the given condition (Query or callable).
        Returns a list of matching documents.
        """
        matched = []
        for doc in self._db_cache[self.name]:
            if callable(cond):
                if cond(doc):
                    matched.append(deepcopy(doc))
            elif isinstance(cond, Query):  # Not strictly necessary, but illustrative
                if cond.test(doc):
                    matched.append(deepcopy(doc))
        return matched

    def get(self, cond=None, doc_id=None):
        """
        Return the first matching document, or None if none match.
        If doc_id is provided, it overrides cond-based lookup.
        """
        if doc_id is not None:
            for doc in self._db_cache[self.name]:
                if doc["_id"] == doc_id:
                    return deepcopy(doc)
            return None

        if cond is None:
            return None

        for doc in self._db_cache[self.name]:
            if callable(cond):
                if cond(doc):
                    return deepcopy(doc)
            elif isinstance(cond, Query):
                if cond.test(doc):
                    return deepcopy(doc)
        return None

    def update(self, fields, cond=None, doc_ids=None):
        """
        Update documents that match cond, or those with specific doc_ids.
        Returns the number of updated documents.
        """
        updated_count = 0
        for index, doc in enumerate(self._db_cache[self.name]):
            if doc_ids is not None:
                if doc["_id"] in doc_ids:
                    self._db_cache[self.name][index].update(fields)
                    updated_count += 1
            else:
                if callable(cond):
                    if cond(doc):
                        self._db_cache[self.name][index].update(fields)
                        updated_count += 1
                elif isinstance(cond, Query):
                    if cond.test(doc):
                        self._db_cache[self.name][index].update(fields)
                        updated_count += 1
        if updated_count > 0:
            self._write()
        return updated_count

    def remove(self, cond=None, doc_ids=None):
        """
        Remove documents that match cond, or those with specific doc_ids.
        Returns the number of removed documents.
        """
        removed_count = 0
        new_table = []
        for doc in self._db_cache[self.name]:
            to_remove = False
            if doc_ids is not None:
                if doc["_id"] in doc_ids:
                    to_remove = True
            else:
                if callable(cond) and cond(doc):
                    to_remove = True
                elif isinstance(cond, Query) and cond.test(doc):
                    to_remove = True
            if to_remove:
                removed_count += 1
            else:
                new_table.append(doc)
        self._db_cache[self.name] = new_table
        if removed_count > 0:
            self._write()
        return removed_count

    def _write(self):
        """
        Write the database cache to disk using the associated storage.
        """
        self._storage.write(self._db_cache)

    def _generate_new_id(self):
        """
        Generate a new integer doc_id. This is naive and scans existing docs.
        """
        existing_ids = [doc["_id"] for doc in self._db_cache[self.name]]
        return (max(existing_ids) + 1) if existing_ids else 1

    def _ensure_doc_ids(self):
        """
        Ensure all documents have an _id field. If any doc lacks it,
        assign one. This maintains backward compatibility if needed.
        """
        changed = False
        max_id = 0
        for doc in self._db_cache[self.name]:
            if "_id" not in doc:
                changed = True
                doc["_id"] = -1  # Temporary placeholder
        if changed:
            # Assign real IDs now
            existing_ids = [doc["_id"] for doc in self._db_cache[self.name] if doc["_id"] != -1]
            max_id = max(existing_ids) if existing_ids else 0
            for doc in self._db_cache[self.name]:
                if doc["_id"] == -1:
                    max_id += 1
                    doc["_id"] = max_id
            self._write()