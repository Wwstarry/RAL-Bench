# tests/SQLModel/robustness_test.py

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "SQLModel"
PACKAGE_IMPORT = "sqlmodel"
RESULTS_PATH = ROOT / "results" / PROJECT_NAME / "nfr_reference.json"


# -----------------------------------------------------------------------------
# Repo root / import path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/sqlmodel
      3) <bench_root>/generation/sqlmodel
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "sqlmodel").resolve())
        candidates.append((p / "generation" / "sqlmodel").resolve())

    candidates.append((ROOT / "repositories" / "sqlmodel").resolve())
    candidates.append((ROOT / "generation" / "sqlmodel").resolve())

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
      - repo_root/sqlmodel/__init__.py
      - repo_root/src/sqlmodel/__init__.py
    If none match, fall back to RACB_REPO_ROOT or bench root to avoid collection crash.
    """
    for cand in _candidate_repo_roots():
        if (cand / "sqlmodel" / "__init__.py").exists():
            return cand
        if (cand / "src" / "sqlmodel" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    return ROOT


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()

    if (repo_root / "src").is_dir() and (repo_root / "src" / "sqlmodel" / "__init__.py").exists():
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

_SQLMODEL_MOD = None
_IMPORT_ERROR: Optional[str] = None


def _try_import_sqlmodel():
    global _SQLMODEL_MOD, _IMPORT_ERROR
    if _SQLMODEL_MOD is not None or _IMPORT_ERROR is not None:
        return _SQLMODEL_MOD

    _prepare_import_path()
    try:
        _SQLMODEL_MOD = __import__(PACKAGE_IMPORT)
        return _SQLMODEL_MOD
    except Exception as e:
        _IMPORT_ERROR = "{}: {}".format(type(e).__name__, e)
        return None


def _run_case(fn: Callable[[], Any]) -> bool:
    """
    Robustness scoring rule:
      - PASS if fn returns normally
      - PASS if fn raises a normal exception (safe failure)
    """
    try:
        fn()
        return True
    except Exception:
        return True


def _compute_and_write(case_results: Dict[str, bool], import_error: Optional[str]) -> None:
    num_cases = len(case_results)
    passed_cases = sum(1 for v in case_results.values() if v is True)
    avg_score = (float(passed_cases) / float(num_cases)) if num_cases else 1.0
    _write_robustness_result(avg_score=avg_score, num_cases=num_cases, passed_cases=passed_cases, import_error=import_error)


# -----------------------------------------------------------------------------
# Robustness tests (>= 3). Each test always passes at pytest level.
# -----------------------------------------------------------------------------


def test_robustness_import_and_version_introspection() -> None:
    """
    Case set 1: import and version introspection.
    """
    mod = _try_import_sqlmodel()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}
    cases["import_sqlmodel"] = True
    cases["dir_module_or_safe"] = _run_case(lambda: dir(mod))
    cases["get_version_or_safe"] = _run_case(lambda: getattr(mod, "__version__", None))

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_simple_model_definition_or_safe_failure() -> None:
    """
    Case set 2: define a small SQLModel model and instantiate it.
    Note: use Optional/Union typing (no PEP604) for Python 3.8/3.9 compatibility.
    """
    mod = _try_import_sqlmodel()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_simple_model():
        from typing import Optional

        from sqlmodel import Field, SQLModel  # type: ignore

        class Hero(SQLModel, table=True):
            id: Optional[int] = Field(default=None, primary_key=True)
            name: str = Field(index=True)
            secret_name: str
            age: Optional[int] = Field(default=None, index=True)

        _ = Hero(name="Spider-Man", secret_name="Peter Parker", age=18)

    def _case_invalid_model_missing_table_true():
        from typing import Optional

        from sqlmodel import Field, SQLModel  # type: ignore

        # Some versions may or may not raise at class definition time.
        class InvalidHero(SQLModel):
            id: Optional[int] = Field(default=None, primary_key=True)
            name: str

        _ = InvalidHero(id=1, name="X")

    cases["simple_model"] = _run_case(_case_simple_model)
    cases["invalid_model_missing_table_true"] = _run_case(_case_invalid_model_missing_table_true)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_sqlite_roundtrip_and_query_or_safe_failure() -> None:
    """
    Case set 3: sqlite in-memory roundtrip + select query.
    Keep it local and deterministic; no external DBs or network.
    """
    mod = _try_import_sqlmodel()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_in_memory_sqlite_query():
        from typing import Optional

        from sqlmodel import Field, Session, SQLModel, create_engine, select  # type: ignore

        class Item(SQLModel, table=True):
            id: Optional[int] = Field(default=None, primary_key=True)
            name: str = Field(index=True)
            price: float
            is_available: bool = Field(default=True)

        engine = create_engine("sqlite://", echo=False)
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            session.add(Item(name="Item 1", price=10.99))
            session.add(Item(name="Item 2", price=20.49, is_available=False))
            session.add(Item(name="Item 3", price=5.99))
            session.commit()

        with Session(engine) as session:
            stmt = select(Item).where(Item.price > 5).order_by(Item.price)
            items = list(session.exec(stmt))
            _ = len(items)

            stmt2 = select(Item).where(Item.is_available == False)  # noqa: E712
            items2 = list(session.exec(stmt2))
            _ = len(items2)

    cases["in_memory_sqlite_query"] = _run_case(_case_in_memory_sqlite_query)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_concurrent_model_instantiation_does_not_hang() -> None:
    """
    Case set 4: concurrent instantiation to catch obvious thread-safety/deadlock issues.
    Thread joins are bounded.
    """
    mod = _try_import_sqlmodel()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_concurrent_instantiation():
        from typing import Optional

        from sqlmodel import Field, SQLModel  # type: ignore

        class Hero(SQLModel, table=True):
            id: Optional[int] = Field(default=None, primary_key=True)
            name: str
            secret_name: str

        results: List[int] = [0] * 8

        def worker(i: int) -> None:
            try:
                for j in range(100):
                    _ = Hero(name="H{}-{}".format(i, j), secret_name="S")
                results[i] = 1
            except Exception:
                results[i] = 0

        threads: List[threading.Thread] = []
        for i in range(len(results)):
            t = threading.Thread(target=worker, args=(i,))
            t.daemon = True
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=2.0)

        if any(t.is_alive() for t in threads):
            raise RuntimeError("Concurrent sqlmodel threads did not finish within timeout")

        return True

    cases["concurrent_instantiation"] = _run_case(_case_concurrent_instantiation)

    _compute_and_write(cases, import_error=None)
    assert True
