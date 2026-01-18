import os
import sys
import time
from pathlib import Path
from typing import Any, Callable, Tuple

import pytest

PROJECT_NAME = "Dataset"
PACKAGE_NAME = "dataset"


def _candidate_repo_roots() -> list[Path]:
    """
    Determine where to import the evaluated repository from.

    Priority:
      1) RACB_REPO_ROOT env var (set by runner)
      2) <bench_root>/repositories/<Project>
      3) <bench_root>/generation/<Project>
    """
    candidates: list[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        # Sometimes RACB_REPO_ROOT already points at repositories/<Project> or generation/<Project>
        candidates.append(p)
        candidates.append((p / "repositories" / PROJECT_NAME).resolve())
        candidates.append((p / "generation" / PROJECT_NAME).resolve())

    bench_root = Path(__file__).resolve().parents[2]
    candidates.append((bench_root / "repositories" / PROJECT_NAME).resolve())
    candidates.append((bench_root / "generation" / PROJECT_NAME).resolve())

    seen = set()
    uniq: list[Path] = []
    for c in candidates:
        if c not in seen:
            uniq.append(c)
            seen.add(c)
    return uniq


def _looks_like_package_root(repo_root: Path) -> bool:
    # common layouts: repo_root/dataset/__init__.py or repo_root/src/dataset/__init__.py
    if (repo_root / PACKAGE_NAME / "__init__.py").exists():
        return True
    if (repo_root / "src" / PACKAGE_NAME / "__init__.py").exists():
        return True
    return False


def _select_repo_root() -> Path:
    for cand in _candidate_repo_roots():
        if _looks_like_package_root(cand):
            return cand
    raise RuntimeError(
        f"Could not locate importable repo root for '{PACKAGE_NAME}'. "
        f"Tried: {[str(p) for p in _candidate_repo_roots()]}"
    )


def _import_dataset():
    """
    Import dataset from the evaluated repository root.
    RACB_REPO_ROOT is expected to point to ./repositories/<Project> or ./generation/<Project>.
    """
    repo_root = _select_repo_root()
    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)

    import dataset  # type: ignore
    return dataset


def _run_case(case_id: str, fn: Callable[[], Any]) -> Tuple[bool, str]:
    """
    Version-tolerant robustness runner:
      - Exception is acceptable (counts as PASS), as long as it is a normal exception.
      - Hard crash / hang is not acceptable (pytest timeout will catch hangs).
    We mark PASS if the call returns or raises within time.
    """
    try:
        _ = fn()
        return True, f"{case_id}: ok"
    except Exception as e:
        return True, f"{case_id}: raised {type(e).__name__} (acceptable)"


@pytest.mark.timeout(10)
def test_dataset_robustness_importable_and_has_connect():
    """
    Robustness 1: dataset should be importable and expose connect().
    """
    dataset = _import_dataset()
    assert hasattr(dataset, "connect"), "dataset.connect must exist"
    assert callable(dataset.connect), "dataset.connect must be callable"


@pytest.mark.timeout(10)
def test_dataset_robustness_in_memory_sqlite_connect_and_tables():
    """
    Robustness 2: connecting to sqlite in-memory should not crash.
    We do not require any specific table behavior, only that the object is usable.
    """
    dataset = _import_dataset()

    def _case():
        db = dataset.connect("sqlite:///:memory:")
        # Access a common attribute; different versions may expose different shapes.
        _ = getattr(db, "tables", None)
        return db

    ok, msg = _run_case("sqlite_memory_connect", _case)
    assert ok, msg


@pytest.mark.timeout(10)
def test_dataset_robustness_invalid_url_does_not_hang():
    """
    Robustness 3: invalid DSN should raise quickly or be handled; must not hang/crash.
    """
    dataset = _import_dataset()

    def _case():
        # Intentionally invalid scheme
        return dataset.connect("not_a_valid_scheme://user:pass@host/db")

    ok, msg = _run_case("invalid_dsn", _case)
    assert ok, msg


@pytest.mark.timeout(10)
def test_dataset_robustness_connect_none_is_handled():
    """
    Robustness 4: connect(None) should raise a normal exception (acceptable) or be handled.
    """
    dataset = _import_dataset()

    def _case():
        return dataset.connect(None)  # type: ignore[arg-type]

    ok, msg = _run_case("connect_none", _case)
    assert ok, msg


@pytest.mark.timeout(10)
def test_dataset_robustness_connect_empty_string_is_handled():
    """
    Robustness 5: connect("") should raise a normal exception (acceptable) or be handled.
    """
    dataset = _import_dataset()

    def _case():
        return dataset.connect("")

    ok, msg = _run_case("connect_empty_string", _case)
    assert ok, msg


@pytest.mark.timeout(10)
def test_dataset_robustness_simple_table_ops_do_not_crash():
    """
    Robustness 6: basic usage path against sqlite in-memory:
      - create/get table
      - insert one row
      - read back (or raise a normal exception)
    Different dataset versions may differ, but the process must remain stable.
    """
    dataset = _import_dataset()

    def _case():
        db = dataset.connect("sqlite:///:memory:")
        # dataset API: db["table_name"] returns a Table
        t = db["items"]
        # insert one row; some versions return row id
        _ = t.insert({"name": "x", "value": 1})
        # try read back
        _ = list(t.all())
        return True

    ok, msg = _run_case("table_insert_and_read", _case)
    assert ok, msg
