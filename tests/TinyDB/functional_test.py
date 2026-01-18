from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pytest

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "tinydb"


def _select_repo_root() -> Path:
    """
    RACB contract:
    - Prefer RACB_REPO_ROOT when provided by the benchmark runner.
    - Fallback to TINYDB_TARGET for local/manual runs.
    """
    override = os.environ.get("RACB_REPO_ROOT", "").strip()
    if override:
        return Path(override).resolve()

    target = os.environ.get("TINYDB_TARGET", "reference").lower()
    if target == "reference":
        return (ROOT / "repositories" / "tinydb").resolve()
    return (ROOT / "generation" / "TinyDB").resolve()


REPO_ROOT = _select_repo_root()
if not REPO_ROOT.exists():
    pytest.skip("Repository root does not exist: {}".format(REPO_ROOT), allow_module_level=True)

src_pkg_init = REPO_ROOT / "src" / PACKAGE / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE / "__init__.py"

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Could not find '{}' package under repo root. Expected {} or {}.".format(
            PACKAGE, src_pkg_init, root_pkg_init
        ),
        allow_module_level=True,
    )

from tinydb import TinyDB, Query, where  # type: ignore  # noqa: E402


def _open_db(tmp_path: Path, filename: str = "db.json") -> TinyDB:
    db_path = tmp_path / filename
    return TinyDB(str(db_path))


def test_insert_and_search(tmp_path: Path) -> None:
    """Basic insert + search on the default table."""
    db_path = tmp_path / "db.json"
    db = TinyDB(str(db_path))

    User = Query()
    db.insert({"name": "Alice", "age": 30})
    db.insert({"name": "Bob", "age": 25})
    db.insert({"name": "Charlie", "age": 35})

    results = db.search(User.age >= 30)
    assert len(results) == 2
    names = {doc["name"] for doc in results}
    assert names == {"Alice", "Charlie"}

    db.close()
    assert db_path.exists()
    assert db_path.stat().st_size > 0


def test_multiple_tables_isolation(tmp_path: Path) -> None:
    """Data in different tables should be isolated."""
    db = _open_db(tmp_path)

    tasks = db.table("tasks")
    logs = db.table("logs")

    tasks.insert({"title": "write code", "done": False})
    tasks.insert({"title": "write tests", "done": False})
    logs.insert({"event": "created_tasks"})

    assert len(tasks) == 2
    assert len(logs) == 1

    all_tasks = tasks.all()
    assert {t["title"] for t in all_tasks} == {"write code", "write tests"}

    db.close()


def test_update_and_remove(tmp_path: Path) -> None:
    """Update and remove operations should work on matching documents."""
    db = _open_db(tmp_path)

    Task = Query()
    table = db.table("tasks")

    table.insert({"title": "task-1", "done": False})
    table.insert({"title": "task-2", "done": False})
    table.insert({"title": "task-3", "done": False})

    table.update({"done": True}, Task.title == "task-2")

    done_tasks = table.search(Task.done == True)  # noqa: E712
    assert len(done_tasks) == 1
    assert done_tasks[0]["title"] == "task-2"

    table.remove(Task.done == True)  # noqa: E712
    remaining = table.all()
    remaining_titles = {t["title"] for t in remaining}
    assert remaining_titles == {"task-1", "task-3"}

    db.close()


def test_where_helper_querying(tmp_path: Path) -> None:
    """where('field') helper should build a working query for search()."""
    db = _open_db(tmp_path)
    db.insert({"name": "Alice", "city": "Tokyo"})
    db.insert({"name": "Bob", "city": "Osaka"})

    results = db.search(where("city") == "Tokyo")
    assert len(results) == 1
    assert results[0]["name"] == "Alice"

    db.close()


def test_get_returns_single_document(tmp_path: Path) -> None:
    """get(query) should retrieve one matching document."""
    db = _open_db(tmp_path)
    User = Query()

    db.insert({"name": "Alice", "age": 30})
    db.insert({"name": "Bob", "age": 25})

    doc = db.get(User.name == "Bob")
    assert doc is not None
    assert doc["name"] == "Bob"
    assert doc["age"] == 25

    db.close()


def test_insert_multiple_and_all(tmp_path: Path) -> None:
    """insert_multiple should add several documents and return their ids."""
    db = _open_db(tmp_path)

    docs = [
        {"k": "a", "v": 1},
        {"k": "b", "v": 2},
        {"k": "c", "v": 3},
    ]
    ids = db.insert_multiple(docs)
    assert isinstance(ids, list)
    assert len(ids) == 3
    assert len(db.all()) == 3

    keys = {d["k"] for d in db.all()}
    assert keys == {"a", "b", "c"}

    db.close()


def test_contains_and_count(tmp_path: Path) -> None:
    """contains and count should reflect stored data and queries."""
    db = _open_db(tmp_path)
    User = Query()

    db.insert({"name": "Alice", "age": 30})
    db.insert({"name": "Bob", "age": 25})
    db.insert({"name": "Charlie", "age": 35})

    assert db.contains(User.name == "Alice") is True
    assert db.contains(User.name == "Dora") is False

    n_ge_30 = db.count(User.age >= 30)
    assert n_ge_30 == 2

    db.close()


def test_persistence_reopen_and_search(tmp_path: Path) -> None:
    """Data should persist on disk and be readable after reopening."""
    db_path = tmp_path / "persist.json"

    db1 = TinyDB(str(db_path))
    db1.insert({"name": "Ada", "lang": "Python"})
    db1.close()

    db2 = TinyDB(str(db_path))
    results = db2.search(where("name") == "Ada")
    assert len(results) == 1
    assert results[0]["lang"] == "Python"
    db2.close()


def test_table_truncate_clears_only_that_table(tmp_path: Path) -> None:
    """truncate on a table should clear its rows without affecting other tables."""
    db = _open_db(tmp_path)

    tasks = db.table("tasks")
    logs = db.table("logs")

    tasks.insert({"title": "t1"})
    tasks.insert({"title": "t2"})
    logs.insert({"event": "created"})

    assert len(tasks) == 2
    assert len(logs) == 1

    tasks.truncate()
    assert len(tasks) == 0
    assert len(logs) == 1

    db.close()


def test_update_by_doc_id(tmp_path: Path) -> None:
    """update with doc_ids should modify the targeted document."""
    db = _open_db(tmp_path)
    table = db.table("items")

    doc_id = table.insert({"name": "ItemA", "qty": 1})
    assert len(table) == 1

    table.update({"qty": 5}, doc_ids=[doc_id])
    updated = table.get(doc_id=doc_id)
    assert updated is not None
    assert updated["name"] == "ItemA"
    assert updated["qty"] == 5

    db.close()


def test_remove_by_doc_id(tmp_path: Path) -> None:
    """remove with doc_ids should delete the targeted document."""
    db = _open_db(tmp_path)
    table = db.table("items")

    id1 = table.insert({"name": "A"})
    id2 = table.insert({"name": "B"})
    assert len(table) == 2

    table.remove(doc_ids=[id1])
    assert len(table) == 1
    remaining = table.all()
    assert remaining[0]["name"] == "B"
    assert table.get(doc_id=id2) is not None

    db.close()


def test_tables_listing_includes_created_tables(tmp_path: Path) -> None:
    """tables() should include table names once they have stored data."""
    db = _open_db(tmp_path)

    t1 = db.table("t1")
    t2 = db.table("t2")
    t1.insert({"x": 1})
    t2.insert({"y": 2})

    names = db.tables()
    # Keep assertion tolerant about whether '_default' exists.
    assert "t1" in names
    assert "t2" in names

    db.close()
