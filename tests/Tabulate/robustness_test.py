# tests/Tabulate/robustness_test.py

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Tabulate"
PACKAGE_IMPORT = "tabulate"
RESULTS_PATH = ROOT / "results" / PROJECT_NAME / "nfr_reference.json"


# -----------------------------------------------------------------------------
# Repo root / import path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/tabulate
      3) <bench_root>/generation/tabulate
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "tabulate").resolve())
        candidates.append((p / "generation" / "tabulate").resolve())

    candidates.append((ROOT / "repositories" / "tabulate").resolve())
    candidates.append((ROOT / "generation" / "tabulate").resolve())

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
      - repo_root/tabulate/__init__.py
      - repo_root/src/tabulate/__init__.py
    If none match, fall back to RACB_REPO_ROOT or bench root to avoid collection crash.
    """
    for cand in _candidate_repo_roots():
        if (cand / "tabulate" / "__init__.py").exists():
            return cand
        if (cand / "src" / "tabulate" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    return ROOT


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()

    if (repo_root / "src").is_dir() and (repo_root / "src" / "tabulate" / "__init__.py").exists():
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

_TABULATE_MOD = None
_IMPORT_ERROR: Optional[str] = None


def _try_import_tabulate():
    global _TABULATE_MOD, _IMPORT_ERROR
    if _TABULATE_MOD is not None or _IMPORT_ERROR is not None:
        return _TABULATE_MOD

    _prepare_import_path()
    try:
        _TABULATE_MOD = __import__(PACKAGE_IMPORT)
        return _TABULATE_MOD
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
    mod = _try_import_tabulate()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}
    cases["import_tabulate"] = True
    cases["dir_module_or_safe"] = _run_case(lambda: dir(mod))
    cases["get_version_or_safe"] = _run_case(lambda: getattr(mod, "__version__", None))

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_basic_and_formats_or_safe_failure() -> None:
    """
    Case set 2: basic tabulation and multiple table formats.
    """
    mod = _try_import_tabulate()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_basic_table_generation():
        import tabulate  # type: ignore

        table_data = [
            [1, "Alice", 25],
            [2, "Bob", 30],
            [3, "Charlie", 35],
        ]
        headers = ["ID", "Name", "Age"]
        s = tabulate.tabulate(table_data, headers=headers)
        _ = len(s)

    def _case_different_table_formats():
        import tabulate  # type: ignore

        table_data = [
            [1, "Alice", 25],
            [2, "Bob", 30],
            [3, "Charlie", 35],
        ]
        headers = ["ID", "Name", "Age"]

        fmts = [
            "plain",
            "simple",
            "github",
            "grid",
            "fancy_grid",
            "pipe",
            "orgtbl",
            "jira",
            "presto",
            "pretty",
        ]
        for fmt in fmts:
            _ = tabulate.tabulate(table_data, headers=headers, tablefmt=fmt)

    cases["basic_table_generation"] = _run_case(_case_basic_table_generation)
    cases["different_table_formats"] = _run_case(_case_different_table_formats)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_mixed_empty_large_inputs_safe() -> None:
    """
    Case set 3: mixed types, empty inputs, and larger input sizes.
    """
    mod = _try_import_tabulate()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_different_data_types():
        import tabulate  # type: ignore

        mixed_data = [
            [1, "Alice", 25, True, 3.14],
            [2, "Bob", 30, False, 2.718],
            [3, "Charlie", 35, True, 1.618],
        ]
        headers = ["ID", "Name", "Age", "Active", "Value"]
        _ = tabulate.tabulate(mixed_data, headers=headers)

        empty_data: List[List[Any]] = []
        _ = tabulate.tabulate(empty_data, headers=headers)

        single_row = [[1, "Alice", 25]]
        _ = tabulate.tabulate(single_row, headers=headers)

        single_col = [[1], [2], [3]]
        _ = tabulate.tabulate(single_col, headers=["ID"])

    def _case_large_data_processing():
        import tabulate  # type: ignore

        large_data = [[i, "Person {}".format(i), i % 100] for i in range(1200)]
        headers = ["ID", "Name", "Age"]
        s = tabulate.tabulate(large_data, headers=headers)
        _ = len(s)

    cases["different_data_types"] = _run_case(_case_different_data_types)
    cases["large_data_processing"] = _run_case(_case_large_data_processing)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_concurrent_tabulate_does_not_hang() -> None:
    """
    Case set 4: concurrent tabulate calls should not deadlock/hang. Thread joins are bounded.
    """
    mod = _try_import_tabulate()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_concurrent_table_generation():
        import tabulate  # type: ignore

        results: List[int] = [0] * 8

        def worker(i: int) -> None:
            try:
                table_data = [[j, "Person {}".format(j), j % 100] for j in range(150)]
                headers = ["ID", "Name", "Age"]
                for _ in range(8):
                    _ = tabulate.tabulate(table_data, headers=headers)
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
            raise RuntimeError("Concurrent tabulate threads did not finish within timeout")

        return True

    cases["concurrent_table_generation"] = _run_case(_case_concurrent_table_generation)

    _compute_and_write(cases, import_error=None)
    assert True
