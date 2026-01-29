from typing import Any, Dict, List, Optional
from .storages import JSONStorage
from .table import Table

class TinyDB:
    """
    Main database object.
    """

    def __init__(self, path: str):
        self._storage = JSONStorage(path)
        self._tables: Dict[str, Table] = {}

    def table(self, name: str) -> Table:
        if name not in self._tables:
            self._tables[name] = Table(name, self._storage)
        return self._tables[name]

    def close(self):
        self._storage.close()

    # --- Task Manager API ---

    @property
    def tasks(self) -> Table:
        return self.table('tasks')

    @property
    def projects(self) -> Table:
        return self.table('projects')

    # --- Analytics ---

    def unfinished_tasks_per_project(self) -> Dict[str, int]:
        """
        Returns a dict: {project_name: count_of_unfinished_tasks}
        """
        projects = self.projects.all()
        result = {}
        for project in projects:
            name = project.get('name')
            count = self.tasks.count(lambda t: t.get('project') == name and t.get('status') != 'done')
            result[name] = count
        return result

    def estimate_per_project(self) -> Dict[str, float]:
        """
        Returns a dict: {project_name: sum_of_estimates_for_unfinished_tasks}
        """
        projects = self.projects.all()
        result = {}
        for project in projects:
            name = project.get('name')
            total = 0.0
            for t in self.tasks.search(lambda t: t.get('project') == name and t.get('status') != 'done'):
                est = t.get('estimate')
                if isinstance(est, (int, float)):
                    total += est
            result[name] = total
        return result