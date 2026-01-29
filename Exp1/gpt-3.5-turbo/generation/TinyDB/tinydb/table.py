import copy
import itertools
from threading import RLock

from .queries import Query


class Table:
    def __init__(self, name, db):
        """
        Table instance.

        :param name: Table name.
        :param db: TinyDB instance.
        """
        self.name = name
        self._db = db
        self._lock = RLock()
        self._last_id = self._calc_last_id()

    def _calc_last_id(self):
        data = self._db._get_table_data(self.name)
        if not data:
            return 0
        return max(item.get('id', 0) for item in data)

    def _get_data(self):
        return self._db._get_table_data(self.name)

    def _write_data(self, data):
        self._db._set_table_data(self.name, data)

    def insert(self, document):
        """
        Insert a new document into the table.

        :param document: dict representing the task or project.
        :return: id of the inserted document.
        """
        with self._lock:
            data = self._get_data()
            self._last_id += 1
            doc = copy.deepcopy(document)
            doc['id'] = self._last_id
            data.append(doc)
            self._write_data(data)
            return doc['id']

    def insert_multiple(self, documents):
        """
        Insert multiple documents.

        :param documents: iterable of dicts.
        :return: list of inserted ids.
        """
        ids = []
        for doc in documents:
            ids.append(self.insert(doc))
        return ids

    def all(self):
        """
        Return all documents.

        :return: list of dicts.
        """
        with self._lock:
            return copy.deepcopy(self._get_data())

    def get(self, cond=None, doc_id=None):
        """
        Get a single document by condition or id.

        :param cond: Query condition.
        :param doc_id: document id.
        :return: dict or None.
        """
        with self._lock:
            data = self._get_data()
            if doc_id is not None:
                for doc in data:
                    if doc.get('id') == doc_id:
                        return copy.deepcopy(doc)
                return None
            if cond is not None:
                for doc in data:
                    if cond(doc):
                        return copy.deepcopy(doc)
            return None

    def search(self, cond):
        """
        Search documents matching condition.

        :param cond: Query condition.
        :return: list of dicts.
        """
        with self._lock:
            data = self._get_data()
            return [copy.deepcopy(doc) for doc in data if cond(doc)]

    def update(self, fields, cond=None, doc_id=None):
        """
        Update documents matching condition or by id.

        :param fields: dict of fields to update.
        :param cond: Query condition.
        :param doc_id: document id.
        :return: number of updated documents.
        """
        updated = 0
        with self._lock:
            data = self._get_data()
            for idx, doc in enumerate(data):
                match = False
                if doc_id is not None and doc.get('id') == doc_id:
                    match = True
                elif cond is not None and cond(doc):
                    match = True
                if match:
                    new_doc = doc.copy()
                    new_doc.update(fields)
                    data[idx] = new_doc
                    updated += 1
            if updated > 0:
                self._write_data(data)
        return updated

    def remove(self, cond=None, doc_id=None):
        """
        Remove documents matching condition or by id.

        :param cond: Query condition.
        :param doc_id: document id.
        :return: number of removed documents.
        """
        removed = 0
        with self._lock:
            data = self._get_data()
            new_data = []
            for doc in data:
                match = False
                if doc_id is not None and doc.get('id') == doc_id:
                    match = True
                elif cond is not None and cond(doc):
                    match = True
                if match:
                    removed += 1
                else:
                    new_data.append(doc)
            if removed > 0:
                self._write_data(new_data)
        return removed

    def count(self, cond=None):
        """
        Count documents matching condition.

        :param cond: Query condition.
        :return: int count.
        """
        with self._lock:
            data = self._get_data()
            if cond is None:
                return len(data)
            return sum(1 for doc in data if cond(doc))

    # Convenience methods for task manager

    def unfinished_tasks_per_project(self):
        """
        Return a dict mapping project name to count of unfinished tasks.

        Assumes documents have 'project' and 'status' fields.
        Status 'done' means finished.

        :return: dict {project_name: count}
        """
        with self._lock:
            data = self._get_data()
            counts = {}
            for doc in data:
                if doc.get('status') != 'done':
                    project = doc.get('project', 'default')
                    counts[project] = counts.get(project, 0) + 1
            return counts