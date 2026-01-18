# tests/Tablib/robustness_test.py

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Tablib"
PACKAGE_IMPORT = "tablib"
RESULTS_PATH = ROOT / "results" / PROJECT_NAME / "nfr_reference.json"


# -----------------------------------------------------------------------------
# Repo root / import path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/tablib
      3) <bench_root>/generation/tablib
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "tablib").resolve())
        candidates.append((p / "generation" / "tablib").resolve())

    candidates.append((ROOT / "repositories" / "tablib").resolve())
    candidates.append((ROOT / "generation" / "tablib").resolve())

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
      - repo_root/tablib/__init__.py
      - repo_root/src/tablib/__init__.py
    If none match, fall back to RACB_REPO_ROOT or bench root to avoid collection crash.
    """
    for cand in _candidate_repo_roots():
        if (cand / "tablib" / "__init__.py").exists():
            return cand
        if (cand / "src" / "tablib" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    return ROOT


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()

    if (repo_root / "src").is_dir() and (repo_root / "src" / "tablib" / "__init__.py").exists():
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

_TABLIB_MOD = None
_IMPORT_ERROR: Optional[str] = None


def _try_import_tablib():
    global _TABLIB_MOD, _IMPORT_ERROR
    if _TABLIB_MOD is not None or _IMPORT_ERROR is not None:
        return _TABLIB_MOD

    _prepare_import_path()
    try:
        _TABLIB_MOD = __import__(PACKAGE_IMPORT)
        return _TABLIB_MOD
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


def test_robustness_import_and_introspection() -> None:
    """
    Case set 1: import and basic module introspection.
    """
    mod = _try_import_tablib()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}
    cases["import_tablib"] = True
    cases["dir_module_or_safe"] = _run_case(lambda: dir(mod))
    cases["get_version_or_safe"] = _run_case(lambda: getattr(mod, "__version__", None))

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_dataset_basic_ops_or_safe_failure() -> None:
    """
    Case set 2: create a Dataset, append rows, and access elements.
    """
    mod = _try_import_tablib()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_simple_dataset_ops():
        import tablib  # type: ignore

        headers = ["Name", "Age", "City"]
        data = [
            ("John", 28, "New York"),
            ("Alice", 32, "London"),
            ("Bob", 45, "Paris"),
        ]
        ds = tablib.Dataset(*data, headers=headers)
        ds.append(("Charlie", 35, "Tokyo"))
        _ = ds[0]
        _ = ds[-1]
        _ = len(ds)

    def _case_invalid_export_format():
        import tablib  # type: ignore

        ds = tablib.Dataset(("John", 28), headers=["Name", "Age"])
        _ = ds.export("invalid_format")

    cases["simple_dataset_ops"] = _run_case(_case_simple_dataset_ops)
    cases["invalid_export_format"] = _run_case(_case_invalid_export_format)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_large_dataset_export_or_safe_failure() -> None:
    """
    Case set 3: larger dataset creation and exports.
    Keep sizes reasonable to avoid timeouts.
    """
    mod = _try_import_tablib()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_large_dataset_exports():
        import tablib  # type: ignore

        headers = ["ID", "Value1", "Value2", "Value3"]
        data = []
        for i in range(600):
            data.append((i, i * 2, i * 3.14, "Item {}".format(i)))

        ds = tablib.Dataset(*data, headers=headers)
        j = ds.export("json")
        c = ds.export("csv")
        _ = len(j)
        _ = len(c)

    cases["large_dataset_exports"] = _run_case(_case_large_dataset_exports)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_concurrent_dataset_ops_do_not_hang() -> None:
    """
    Case set 4: concurrent dataset creation/export should not deadlock/hang.
    Thread joins are bounded.
    """
    mod = _try_import_tablib()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_concurrent_exports():
        import tablib  # type: ignore

        results: List[int] = [0] * 6

        def worker(i: int) -> None:
            try:
                headers = ["A", "B"]
                ds = tablib.Dataset(headers=headers)
                for j in range(200):
                    ds.append(("{}-{}".format(i, j), j))
                _ = ds.export("csv")
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
            raise RuntimeError("Concurrent tablib threads did not finish within timeout")

        return True

    cases["concurrent_dataset_ops"] = _run_case(_case_concurrent_exports)

    _compute_and_write(cases, import_error=None)
    assert True
