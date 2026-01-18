from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, List, Sequence

import pytest

ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT_ENV = "RACB_REPO_ROOT"
TARGET_ENV_VAR = "DATASET_TARGET"
PACKAGE_NAME = "dataset"


def _candidate_repo_roots() -> List[Path]:
    cands: List[Path] = []

    override = os.environ.get(REPO_ROOT_ENV)
    if override:
        base = Path(override).resolve()
        cands.extend(
            [
                base,
                (base / "src").resolve(),
                (base / "repositories" / "dataset").resolve(),
                (base / "repositories" / "Dataset").resolve(),
                (base / "generation" / "dataset").resolve(),
                (base / "generation" / "Dataset").resolve(),
            ]
        )

    target = os.environ.get(TARGET_ENV_VAR, "reference").lower()
    if target in ("reference", "ref"):
        cands.extend(
            [
                (ROOT / "repositories" / "dataset").resolve(),
                (ROOT / "repositories" / "Dataset").resolve(),
            ]
        )
    elif target in ("generated", "generation", "gen"):
        cands.extend(
            [
                (ROOT / "generation" / "dataset").resolve(),
                (ROOT / "generation" / "Dataset").resolve(),
            ]
        )

    for base in [(ROOT / "repositories").resolve(), (ROOT / "generation").resolve()]:
        if not base.exists():
            continue
        try:
            for init_py in base.rglob(str(Path(PACKAGE_NAME) / "__init__.py")):
                cands.append(init_py.parent.parent.resolve())
        except Exception:
            pass
        try:
            for init_py in base.rglob(str(Path("src") / PACKAGE_NAME / "__init__.py")):
                cands.append(init_py.parent.parent.parent.resolve())
        except Exception:
            pass

    seen = set()
    uniq: List[Path] = []
    for p in cands:
        if p not in seen:
            uniq.append(p)
            seen.add(p)
    return uniq


def _looks_importable(repo_root: Path) -> bool:
    if not repo_root.exists():
        return False
    if (repo_root / PACKAGE_NAME / "__init__.py").exists():
        return True
    if (repo_root / "src" / PACKAGE_NAME / "__init__.py").exists():
        return True
    return False


def _select_repo_root() -> Path:
    tried = _candidate_repo_roots()
    for cand in tried:
        if _looks_importable(cand):
            return cand
    raise RuntimeError(f"Repository root does not exist or is not importable (checked): {tried!r}")


REPO_ROOT = _select_repo_root()


def _ensure_import_path(repo_root: Path) -> None:
    src = repo_root / "src"
    sys_path_entry = str(src) if (src / PACKAGE_NAME / "__init__.py").exists() else str(repo_root)
    if sys_path_entry not in sys.path:
        sys.path.insert(0, sys_path_entry)


_ensure_import_path(REPO_ROOT)

import dataset  # type: ignore[import]  # noqa: E402


def create_in_memory_db() -> Any:
    return dataset.connect("sqlite:///:memory:")


def _table_columns(table: Any) -> Sequence[str]:
    cols = getattr(table, "columns", None)
    if cols is None:
        return []
    try:
        return list(cols)
    except Exception:
        return []


def _db_tables(db: Any) -> List[str]:
    t = getattr(db, "tables", None)
    if t is None:
        return []
    try:
        if callable(t):
            return list(t())
        return list(t)
    except Exception:
        return []


def _table_name(table: Any, fallback: str) -> str:
    n = getattr(table, "name", None)
    if isinstance(n, str) and n:
        return n
    return fallback


def test_insert_and_query_basic_rows() -> None:
    db = create_in_memory_db()
    table = db["users"]

    table.insert({"name": "Alice", "age": 30, "country": "DE"})
    table.insert({"name": "Bob", "age": 41, "country": "US", "active": True})
    table.insert({"name": "Charlie", "age": 41, "country": "US", "active": False})

    assert "id" in _table_columns(table)
    assert "name" in _table_columns(table)
    assert "country" in _table_columns(table)
    assert len(table) == 3

    alice = table.find_one(name="Alice")
    assert alice is not None
    assert alice["country"] == "DE"

    older = list(table.find(age={">=": 40}))
    assert {row["name"] for row in older} == {"Bob", "Charlie"}

    distinct_countries = list(table.distinct("country"))
    countries = {row["country"] for row in distinct_countries}
    assert countries == {"DE", "US"}

    table.delete(country="DE")
    remaining = {row["name"] for row in table.all()}
    assert remaining == {"Bob", "Charlie"}


def test_update_upsert_and_indexes() -> None:
    db = create_in_memory_db()
    table = db["accounts"]

    rows = [
        {"account_id": 1, "owner": "Alice", "balance": 100.0, "currency": "EUR"},
        {"account_id": 2, "owner": "Bob", "balance": 250.0, "currency": "USD"},
    ]
    table.insert_many(rows)

    if hasattr(table, "create_index") and hasattr(table, "has_index"):
        table.create_index(["owner", "currency"])
        assert table.has_index(["owner", "currency"])

    table.update({"account_id": 1, "balance": 150.0}, ["account_id"])
    updated = table.find_one(account_id=1)
    assert updated is not None
    assert pytest.approx(updated["balance"]) == 150.0

    table.upsert({"account_id": 2, "balance": 275.0}, ["account_id"])
    table.upsert({"account_id": 3, "owner": "Charlie", "balance": 50.0}, ["account_id"])

    assert len(table) == 3
    acc2 = table.find_one(account_id=2)
    acc3 = table.find_one(account_id=3)
    assert acc2 is not None and pytest.approx(acc2["balance"]) == 275.0
    assert acc3 is not None and acc3["owner"] == "Charlie"


def test_transactions_commit_and_rollback(tmp_path: Path) -> None:
    db_path = tmp_path / "tx_sample.db"
    db_url = "sqlite:///%s" % str(db_path)
    db = dataset.connect(db_url)
    table = db["events"]

    db.begin()
    table.insert({"name": "committed", "category": "ok"})
    db.commit()
    assert table.count(name="committed") == 1

    db.begin()
    table.insert({"name": "rolled_back", "category": "fail"})
    db.rollback()
    assert table.count(name="rolled_back") == 0

    results = list(db.query("SELECT category, COUNT(*) as c FROM events GROUP BY category"))
    assert len(results) == 1
    assert results[0]["category"] == "ok"
    assert int(results[0]["c"]) == 1


def test_insert_many_returns_ids_and_count() -> None:
    db = create_in_memory_db()
    table = db["items"]

    rows = [{"name": "A"}, {"name": "B"}, {"name": "C"}]
    ret = table.insert_many(rows)

    assert len(table) == 3
    if ret is not None:
        try:
            ids = list(ret)
            assert len(ids) == 3
        except TypeError:
            assert True


def test_find_one_missing_returns_none() -> None:
    db = create_in_memory_db()
    table = db["t"]
    table.insert({"name": "only"})
    missing = table.find_one(name="absent")
    assert missing is None


def test_find_order_by_limit_offset() -> None:
    db = create_in_memory_db()
    table = db["nums"]
    for i in range(10):
        table.insert({"n": i})

    rows = list(table.find(order_by="n", _limit=3, _offset=4))
    assert [r["n"] for r in rows] == [4, 5, 6]


def test_table_all_iteration_and_row_shape() -> None:
    db = create_in_memory_db()
    table = db["people"]
    table.insert({"name": "Alice", "age": 30})
    table.insert({"name": "Bob", "age": 31})

    rows = list(table.all())
    assert len(rows) == 2
    assert all(("id" in r and "name" in r) for r in rows)


def test_delete_and_clear_all_rows() -> None:
    """
    Older dataset.Table may not expose truncate().
    Clear a table and end at 0 rows without relying on result iteration for DML.
    """
    db = create_in_memory_db()
    table = db["logs"]
    table.insert_many([{"kind": "a"}, {"kind": "b"}, {"kind": "b"}])

    assert len(table) == 3
    table.delete(kind="a")
    assert len(table) == 2
    assert table.count(kind="b") == 2

    if hasattr(table, "truncate"):
        table.truncate()
    else:
        # Use db.executable.execute (SQLAlchemy connection/engine) for DML
        name = _table_name(table, "logs")
        executable = getattr(db, "executable", None)
        if executable is not None and hasattr(executable, "execute"):
            executable.execute("DELETE FROM %s" % name)
        else:
            # Last-resort fallback: delete rows we can see (slower but safe)
            for row in list(table.all()):
                if "id" in row:
                    table.delete(id=row["id"])
                else:
                    table.delete(**row)

    assert len(table) == 0


def test_drop_table_removes_from_db_tables() -> None:
    db = create_in_memory_db()
    table = db["to_drop"]
    table.insert({"x": 1})

    assert "to_drop" in _db_tables(db)

    if hasattr(table, "drop"):
        table.drop()
    else:
        executable = getattr(db, "executable", None)
        if executable is not None and hasattr(executable, "execute"):
            executable.execute("DROP TABLE to_drop")
        else:
            _ = list(db.query("DROP TABLE to_drop"))

    assert "to_drop" not in _db_tables(db)


def test_raw_sql_query_with_parameters(tmp_path: Path) -> None:
    db_path = tmp_path / "param.db"
    db = dataset.connect("sqlite:///%s" % str(db_path))
    table = db["kv"]
    table.insert_many([{"k": "a", "v": 1}, {"k": "b", "v": 2}])

    rows = list(db.query("SELECT k, v FROM kv WHERE v >= :min_v ORDER BY v", min_v=2))
    assert len(rows) == 1
    assert rows[0]["k"] == "b"
    assert int(rows[0]["v"]) == 2


def test_distinct_returns_unique_values() -> None:
    db = create_in_memory_db()
    table = db["colors"]
    table.insert_many([{"c": "red"}, {"c": "red"}, {"c": "blue"}])

    distinct = list(table.distinct("c"))
    values = {r["c"] for r in distinct}
    assert values == {"red", "blue"}
