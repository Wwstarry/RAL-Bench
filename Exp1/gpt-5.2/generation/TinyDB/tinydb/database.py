from __future__ import annotations

import threading
from typing import Any, Dict, Optional

from .storages import JSONStorage
from .table import Table
from .queries import Query, where


class Database:
    """
    Database wraps a JSONStorage and provides named tables.

    Example:
        db = Database("tasks.json")
        tasks = db.table("tasks")
        tid = tasks.create_task("Write docs", project="core", estimate=2)
        open_core = tasks.search((where("project") == "core") & (where("status") != "done"))
    """

    def __init__(self, path: str, *, storage: Optional[JSONStorage] = None):
        self._storage = storage or JSONStorage(path)
        self._lock = threading.RLock()
        self._tables: Dict[str, Table] = {}

    def table(self, name: str) -> Table:
        if name not in self._tables:
            self._tables[name] = Table(self, name)
        return self._tables[name]

    # Convenience for task manager usage
    @property
    def tasks(self) -> Table:
        return self.table("tasks")

    # ---------- analytics-like helpers ----------
    def unfinished_tasks_per_project(self, *, table: str = "tasks") -> Dict[str, int]:
        t = self.table(table)
        rows = t.search(where("status") != "done")
        out: Dict[str, int] = {}
        for r in rows:
            proj = r.get("project") or "inbox"
            out[str(proj)] = out.get(str(proj), 0) + 1
        return out

    def total_estimate_per_project(self, *, table: str = "tasks", only_unfinished: bool = False) -> Dict[str, float]:
        t = self.table(table)
        q: Optional[Query] = (where("status") != "done") if only_unfinished else None
        rows = t.search(q)
        out: Dict[str, float] = {}
        for r in rows:
            proj = str(r.get("project") or "inbox")
            est = r.get("estimate")
            try:
                est_f = float(est)
            except Exception:
                est_f = 0.0
            out[proj] = out.get(proj, 0.0) + est_f
        return out

    def project_summary(self, project: str, *, table: str = "tasks") -> Dict[str, Any]:
        t = self.table(table)
        rows = t.search(where("project") == project)
        total = len(rows)
        done = sum(1 for r in rows if r.get("status") == "done")
        todo = total - done
        est_total = 0.0
        est_open = 0.0
        for r in rows:
            est = r.get("estimate")
            try:
                est_f = float(est)
            except Exception:
                est_f = 0.0
            est_total += est_f
            if r.get("status") != "done":
                est_open += est_f
        return {
            "project": project,
            "total_tasks": total,
            "done_tasks": done,
            "open_tasks": todo,
            "estimate_total": est_total,
            "estimate_open": est_open,
        }

    # ---------- maintenance ----------
    def close(self) -> None:
        # No open handles for JSONStorage; kept for API symmetry.
        return

    def dump(self) -> Dict[str, Any]:
        with self._lock:
            return self._storage.read()