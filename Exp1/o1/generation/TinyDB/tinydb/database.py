import os
from .storages import JSONStorage
from .table import Table

class TinyDB:
    """
    A lightweight JSON-based database. Stores data in a JSON file.
    Each table is stored as a key in the master in-memory dictionary.
    """

    def __init__(self, path, storage_cls=JSONStorage):
        self._storage = storage_cls(path)
        self._db_cache = self._storage.read() or {}
        self._tables = {}

    def table(self, name):
        """
        Retrieve (or create) a table with the given name.
        """
        if name not in self._tables:
            if name not in self._db_cache:
                self._db_cache[name] = []
            self._tables[name] = Table(name, self._db_cache, self._storage)
        return self._tables[name]

    def close(self):
        """
        Ensure changes are written to disk and close any open resources.
        """
        self._storage.write(self._db_cache)
        self._storage.close()

class TaskManager:
    """
    High-level API for managing tasks with an underlying TinyDB instance.
    """

    def __init__(self, db_path="tasks.json"):
        self.db = TinyDB(db_path)
        self.tasks_table = self.db.table("tasks")

    def create_task(self, title, project, estimate=0, status="open"):
        """
        Create a new task and store it in the tasks table.
        """
        task = {
            "title": title,
            "project": project,
            "estimate": estimate,
            "status": status
        }
        return self.tasks_table.insert(task)

    def update_task(self, task_id, **updates):
        """
        Update an existing task by its doc_id with given fields.
        """
        return self.tasks_table.update(updates, doc_ids=[task_id])

    def delete_task(self, task_id):
        """
        Delete a task by its doc_id.
        """
        return self.tasks_table.remove(doc_ids=[task_id])

    def get_task(self, task_id):
        """
        Retrieve a single task by doc_id.
        """
        return self.tasks_table.get(doc_id=task_id)

    def list_tasks(self, project=None, status=None):
        """
        List all tasks, optionally filtering by project or status.
        """
        all_tasks = self.tasks_table.all()
        if project:
            all_tasks = [t for t in all_tasks if t.get("project") == project]
        if status:
            all_tasks = [t for t in all_tasks if t.get("status") == status]
        return all_tasks

    def unfinished_tasks_per_project(self):
        """
        Return a dictionary of {project_name: count_of_unfinished_tasks, ...}.
        """
        all_tasks = self.tasks_table.all()
        counts = {}
        for task in all_tasks:
            if task.get("status") != "done":
                proj = task.get("project", "Unknown")
                counts[proj] = counts.get(proj, 0) + 1
        return counts

    def close(self):
        """
        Close the underlying database.
        """
        self.db.close()