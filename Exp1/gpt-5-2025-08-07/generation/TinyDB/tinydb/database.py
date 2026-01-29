from typing import Any, Dict, Iterable, List, Optional, Union

from .storages import JSONStorage, Storage
from .table import Table


class Database:
    def __init__(self, storage: Union[str, Storage]) -> None:
        if isinstance(storage, str):
            self._storage: Storage = JSONStorage(storage)
        else:
            self._storage = storage
        self._data: Dict[str, Any] = self._storage.read() or {"tables": {}}
        if "tables" not in self._data:
            self._data["tables"] = {}
        self._tables: Dict[str, Table] = {}

    def table(self, name: str) -> Table:
        if name not in self._tables:
            # Ensure table exists in data
            if name not in self._data["tables"]:
                self._data["tables"][name] = {"docs": [], "next_id": 1}
                self._save()
            self._tables[name] = Table(self, name)
        return self._tables[name]

    def tables(self) -> List[str]:
        return list(self._data.get("tables", {}).keys())

    def drop_table(self, name: str) -> None:
        if name in self._tables:
            del self._tables[name]
        if name in self._data.get("tables", {}):
            del self._data["tables"][name]
            self._save()

    def _save(self) -> None:
        self._storage.write(self._data)

    def close(self) -> None:
        self._storage.close()


# Domain-specific helper: TaskManager built atop Database
from datetime import datetime
from .queries import where, Query


class TaskManager:
    def __init__(self, path: str) -> None:
        self.db = Database(path)
        self.tasks = self.db.table("tasks")
        self.projects = self.db.table("projects")

    # Project operations
    def create_project(self, name: str, **attrs: Any) -> int:
        existing = self.projects.get(where("name") == name)
        if existing:
            return existing["id"]
        doc = {"name": name, "created_at": datetime.utcnow().isoformat(timespec="seconds")}
        doc.update(attrs)
        return self.projects.insert(doc)

    def get_project(self, name: str) -> Optional[Dict[str, Any]]:
        return self.projects.get(where("name") == name)

    def list_projects(self) -> List[Dict[str, Any]]:
        return self.projects.all()

    def delete_project(self, name: str) -> int:
        return self.projects.remove(where("name") == name)

    # Task operations
    def create_task(
        self,
        title: str,
        project: Optional[str] = None,
        status: str = "todo",
        estimate: Optional[float] = None,
        **attrs: Any,
    ) -> int:
        doc: Dict[str, Any] = {
            "title": title,
            "project": project,
            "status": status,
            "estimate": estimate,
            "created_at": datetime.utcnow().isoformat(timespec="seconds"),
        }
        doc.update(attrs)
        return self.tasks.insert(doc)

    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        return self.tasks.get(doc_id=task_id)

    def list_tasks(
        self,
        project: Optional[str] = None,
        status: Optional[str] = None,
        filters: Optional[Union[Dict[str, Any], Query]] = None,
    ) -> List[Dict[str, Any]]:
        q: Optional[Query] = None
        if project is not None:
            q = where("project") == project
        if status is not None:
            q = (q & (where("status") == status)) if q is not None else (where("status") == status)
        if filters is not None:
            if isinstance(filters, Query):
                q = (q & filters) if q is not None else filters
            elif isinstance(filters, dict):
                # Add equality matches
                for k, v in filters.items():
                    term = where(k) == v
                    q = (q & term) if q is not None else term
            else:
                raise TypeError("filters must be dict or Query")
        return self.tasks.search(q)

    def update_task(self, task_id: int, **updates: Any) -> int:
        if "id" in updates:
            updates.pop("id")
        return self.tasks.update(updates, doc_ids=[task_id])

    def delete_task(self, task_id: int) -> int:
        return self.tasks.remove(doc_ids=[task_id])

    def search_tasks(self, query: Query) -> List[Dict[str, Any]]:
        return self.tasks.search(query)

    # Analytics
    def unfinished_tasks_per_project(self, done_statuses: Optional[Iterable[str]] = None) -> Dict[str, int]:
        done = set(s.lower() for s in (done_statuses or ["done", "completed", "closed"]))
        counts: Dict[str, int] = {}
        for task in self.tasks.all():
            status = str(task.get("status", "")).lower()
            if status in done:
                continue
            project = task.get("project") or "unassigned"
            counts[project] = counts.get(project, 0) + 1
        return counts

    def estimates_per_project(self, unfinished_only: bool = False, done_statuses: Optional[Iterable[str]] = None) -> Dict[str, float]:
        done = set(s.lower() for s in (done_statuses or ["done", "completed", "closed"]))
        sums: Dict[str, float] = {}
        for task in self.tasks.all():
            status = str(task.get("status", "")).lower()
            if unfinished_only and status in done:
                continue
            est = task.get("estimate")
            if est is None:
                continue
            try:
                val = float(est)
            except (TypeError, ValueError):
                continue
            project = task.get("project") or "unassigned"
            sums[project] = sums.get(project, 0.0) + val
        return sums

    def counts_by_status(self, project: Optional[str] = None) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        tasks = self.tasks.all() if project is None else self.tasks.search(where("project") == project)
        for t in tasks:
            status = str(t.get("status", "") or "").lower() or "unknown"
            counts[status] = counts.get(status, 0) + 1
        return counts

    def close(self) -> None:
        self.db.close()