from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Dict, Any

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("TINYDB_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "tinydb"
else:
    REPO_ROOT = ROOT / "generation" / "TinyDB"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tinydb import TinyDB, Query  # type: ignore  # noqa: E402


def _build_task_database(db_path: Path, num_tasks: int = 300) -> Dict[str, Any]:
    """
    Build a small "personal task manager" database using TinyDB.

    This is used as an end-to-end workload for resource / integration tests.
    """
    db = TinyDB(db_path)
    Task = Query()

    tasks_table = db.table("tasks")
    projects_table = db.table("projects")

    # Create some projects
    projects = [
        {"key": "proj-docs", "name": "Write docs"},
        {"key": "proj-code", "name": "Implement features"},
    ]
    for proj in projects:
        projects_table.insert(proj)

    num_projects = len(projects_table)

    # Create many tasks distributed across projects
    for i in range(num_tasks):
        project_key = "proj-docs" if i % 2 == 0 else "proj-code"
        tasks_table.insert(
            {
                "id": f"T-{i:04d}",
                "title": f"Task {i}",
                "project": project_key,
                "done": i % 5 == 0,
                "estimate": (i % 8) + 1,
            }
        )

    # Query: all unfinished tasks for proj-docs
    unfinished_docs = tasks_table.search(
        (Task.project == "proj-docs") & (Task.done == False)  # noqa: E712
    )
    unfinished_docs_initial = len(unfinished_docs)

    # Mark some tasks as done
    tasks_table.update({"done": True}, Task.estimate >= 7)

    # Delete all tasks that are marked done and have low estimate
    tasks_table.remove((Task.done == True) & (Task.estimate <= 3))  # noqa: E712

    remaining_tasks_list = tasks_table.all()
    remaining_tasks = len(remaining_tasks_list)

    db.close()

    return {
        "db_path": db_path,
        "num_projects": num_projects,
        "initial_tasks": num_tasks,
        "unfinished_docs_initial": unfinished_docs_initial,
        "remaining_tasks": remaining_tasks,
    }


def test_task_database_integration(tmp_path: Path) -> None:
    """
    End-to-end integration test for TinyDB as a local task manager backend.
    """
    db_path = tmp_path / "tasks.json"
    stats = _build_task_database(db_path, num_tasks=250)

    assert db_path.exists()
    assert db_path.stat().st_size > 0

    # We created exactly 2 projects
    assert stats["num_projects"] == 2

    # We should have some unfinished documentation tasks initially
    assert stats["unfinished_docs_initial"] > 0

    # Some tasks should remain after updates and removals
    assert 0 < stats["remaining_tasks"] < stats["initial_tasks"]
