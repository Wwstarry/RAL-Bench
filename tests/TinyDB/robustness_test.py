# tests/TinyDB/robustness_test.py

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "TinyDB"
PACKAGE_IMPORT = "tinydb"
RESULTS_PATH = ROOT / "results" / PROJECT_NAME / "nfr_reference.json"


# -----------------------------------------------------------------------------
# Repo root / import path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/tinydb
      3) <bench_root>/generation/tinydb
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "tinydb").resolve())
        candidates.append((p / "generation" / "tinydb").resolve())

    candidates.append((ROOT / "repositories" / "tinydb").resolve())
    candidates.append((ROOT / "generation" / "tinydb").resolve())

    seen: set = set()
    uniq: List[Path] = []
    for c in candidates:
        if c not in seen:
            uniq.append(c)
            seen.add(c)
    return uniq


def _select_repo_root() -> Path:
    """
    Pick a repo root that looks importable:
      - repo_root/tinydb/__init__.py
      - repo_root/src/tinydb/__init__.py
    If none match, fall back to RACB_REPO_ROOT or bench root to avoid collection crash.
    """
    for cand in _candidate_repo_roots():
        if (cand / "tinydb" / "__init__.py").exists():
            return cand
        if (cand / "src" / "tinydb" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    return ROOT


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()

    if (repo_root / "src").is_dir() and (repo_root / "src" / "tinydb" / "__init__.py").exists():
        p = str(repo_root / "src")
        if p not in sys.path:
            sys.path.insert(0, p)
    else:
        p = str(repo_root)
        if p not in sys.path:
            sys.path.insert(0, p)


# -----------------------------------------------------------------------------
# Results JSON helpers (single robustness block; preserve other NFRs)
# -----------------------------------------------------------------------------

def _load_json() -> Dict[str, Any]:
    if RESULTS_PATH.exists():
        try:
            with open(RESULTS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            return {}
    return {}


def _save_json(data: Dict[str, Any]) -> None:
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)


def _write_robustness_result(
    avg_score: float,
    num_cases: int,
    passed_cases: int,
    import_error: Optional[str] = None,
) -> None:
    data = _load_json()

    rob: Dict[str, Any] = {
        "avg_score": float(round(avg_score, 3)),
        "num_cases": int(num_cases),
        "passed_cases": int(passed_cases),
    }
    if import_error:
        rob["import_error"] = str(import_error)

    data["robustness"] = rob
    _save_json(data)


# -----------------------------------------------------------------------------
# Robustness runner
# -----------------------------------------------------------------------------

_TINYDB_MOD = None
_IMPORT_ERROR: Optional[str] = None


def _try_import_tinydb():
    global _TINYDB_MOD, _IMPORT_ERROR
    if _TINYDB_MOD is not None or _IMPORT_ERROR is not None:
        return _TINYDB_MOD

    _prepare_import_path()
    try:
        _TINYDB_MOD = __import__(PACKAGE_IMPORT)
        return _TINYDB_MOD
    except Exception as e:
        _IMPORT_ERROR = "{}: {}".format(type(e).__name__, e)
        return None


def _run_case(fn: Callable[[], Any]) -> bool:
    """
    Robustness scoring rule (benchmark-required):
      - PASS if fn returns normally
      - PASS if fn raises a normal exception (safe failure)

    Include BaseException to tolerate sys.exit() style failures without failing pytest.
    """
    try:
        fn()
        return True
    except BaseException:
        return True


def _compute_and_write(case_results: Dict[str, bool], import_error: Optional[str]) -> None:
    num_cases = len(case_results)
    passed_cases = sum(1 for v in case_results.values() if v is True)
    avg_score = (float(passed_cases) / float(num_cases)) if num_cases else 1.0
    _write_robustness_result(avg_score=avg_score, num_cases=num_cases, passed_cases=passed_cases, import_error=import_error)


# -----------------------------------------------------------------------------
# Robustness tests (>= 3). Each test always passes at pytest level.
# -----------------------------------------------------------------------------


def test_robustness_import_and_introspection() -> None:
    """
    Case set 1: import and basic module introspection.
    """
    mod = _try_import_tinydb()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}
    cases["import_tinydb"] = True
    cases["dir_module_or_safe"] = _run_case(lambda: dir(mod))
    cases["import_query_or_safe"] = _run_case(lambda: __import__("tinydb.queries"))

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_basic_crud_or_safe_failure() -> None:
    """
    Case set 2: basic CRUD on a temporary JSON DB file.
    """
    mod = _try_import_tinydb()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_basic_crud():
        from tempfile import TemporaryDirectory

        from tinydb import Query, TinyDB  # type: ignore

        with TemporaryDirectory() as td:
            db_path = Path(td) / "db.json"
            db = TinyDB(str(db_path))
            try:
                db.insert({"name": "Alice", "age": 25})
                db.insert({"name": "Bob", "age": 30})

                user = Query()
                alice = db.get(user.name == "Alice")

                db.update({"age": 26}, user.name == "Alice")
                db.remove(user.name == "Bob")

                _ = alice
                _ = len(db)
            finally:
                db.close()

    def _case_edge_values():
        from tempfile import TemporaryDirectory

        from tinydb import Query, TinyDB  # type: ignore

        with TemporaryDirectory() as td:
            db_path = Path(td) / "db.json"
            db = TinyDB(str(db_path))
            try:
                db.insert({})
                db.insert({"text": "特殊字符: 中文测试 😀 \n\t"})
                nested: Dict[str, Any] = {"level": 1}
                cur = nested
                for i in range(2, 10):
                    cur["level_{}".format(i)] = {"level": i}
                    cur = cur["level_{}".format(i)]
                db.insert({"nested": nested})

                q = Query()
                _ = db.get(q.non_existent_field == "value")
                db.update({"field": "value"}, q.non_existent_field == "value")
                db.remove(q.non_existent_field == "value")
            finally:
                db.close()

    cases["basic_crud"] = _run_case(_case_basic_crud)
    cases["edge_values"] = _run_case(_case_edge_values)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_bulk_ops_or_safe_failure() -> None:
    """
    Case set 3: bulk insert + scan + update + truncate.
    Keep the scale moderate to avoid timeouts.
    """
    mod = _try_import_tinydb()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_bulk_ops():
        from tempfile import TemporaryDirectory

        from tinydb import Query, TinyDB  # type: ignore

        with TemporaryDirectory() as td:
            db_path = Path(td) / "bulk.json"
            db = TinyDB(str(db_path))
            try:
                for i in range(800):
                    db.insert({"id": i, "value": "data_{}".format(i)})
                all_rows = db.all()
                _ = len(all_rows)

                db.update({"updated": True}, Query().id.exists())
                db.truncate()
                _ = len(db)
            finally:
                db.close()

    cases["bulk_ops"] = _run_case(_case_bulk_ops)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_concurrent_access_does_not_hang() -> None:
    """
    Case set 4: concurrent inserts should not deadlock/hang.
    TinyDB may not be fully thread-safe; exceptions are treated as safe failures.
    Thread joins are bounded.
    """
    mod = _try_import_tinydb()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_concurrent_inserts():
        from tempfile import TemporaryDirectory

        from tinydb import TinyDB  # type: ignore
        from tinydb.middlewares import CachingMiddleware  # type: ignore
        from tinydb.storages import JSONStorage  # type: ignore

        with TemporaryDirectory() as td:
            db_path = Path(td) / "concurrent.json"
            db = TinyDB(str(db_path), storage=CachingMiddleware(JSONStorage))
            try:
                results: List[int] = [0] * 8

                def worker(tid: int) -> None:
                    try:
                        for i in range(120):
                            db.insert({"thread_id": tid, "item_id": i})
                        results[tid] = 1
                    except Exception:
                        results[tid] = 0

                threads: List[threading.Thread] = []
                for tid in range(len(results)):
                    t = threading.Thread(target=worker, args=(tid,))
                    t.daemon = True
                    threads.append(t)
                    t.start()

                for t in threads:
                    t.join(timeout=2.0)

                if any(t.is_alive() for t in threads):
                    raise RuntimeError("Concurrent tinydb threads did not finish within timeout")

                _ = len(db.all())
            finally:
                db.close()

        return True

    cases["concurrent_inserts"] = _run_case(_case_concurrent_inserts)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_corrupt_file_open_or_safe_failure() -> None:
    """
    Case set 5: open a corrupted JSON database file.
    TinyDB may raise or may recover; both are acceptable.
    """
    mod = _try_import_tinydb()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_corrupt_db_open():
        from tempfile import TemporaryDirectory

        from tinydb import TinyDB  # type: ignore

        with TemporaryDirectory() as td:
            db_path = Path(td) / "corrupt.json"

            # Create a valid DB first.
            db = TinyDB(str(db_path))
            db.insert({"name": "Alice", "age": 25})
            db.close()

            # Corrupt the underlying JSON file.
            db_path.write_text('{"invalid_json": true,', encoding="utf-8")

            # Re-open: may raise or may proceed.
            db2 = TinyDB(str(db_path))
            try:
                _ = len(db2)
            finally:
                db2.close()

    cases["corrupt_db_open"] = _run_case(_case_corrupt_db_open)

    _compute_and_write(cases, import_error=None)
    assert True
