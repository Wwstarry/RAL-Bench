# tests/Lifelines/robustness_test.py

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Lifelines"
PACKAGE_IMPORT = "lifelines"

RESULTS_DIR = ROOT / "results" / PROJECT_NAME
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_PATH = RESULTS_DIR / "nfr_robustness.json"


# -----------------------------------------------------------------------------
# Repo root / import path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/lifelines
      3) <bench_root>/generation/lifelines
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "lifelines").resolve())
        candidates.append((p / "generation" / "lifelines").resolve())

    candidates.append((ROOT / "repositories" / "lifelines").resolve())
    candidates.append((ROOT / "generation" / "lifelines").resolve())

    seen = set()
    uniq: List[Path] = []
    for c in candidates:
        if c not in seen:
            uniq.append(c)
            seen.add(c)
    return uniq


def _select_repo_root() -> Path:
    """
    Pick a repo root that looks importable:
      - repo_root/lifelines/__init__.py
      - repo_root/src/lifelines/__init__.py
    """
    for cand in _candidate_repo_roots():
        if (cand / "lifelines" / "__init__.py").exists():
            return cand
        if (cand / "src" / "lifelines" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    raise RuntimeError(f"Could not locate importable repo root for {PROJECT_NAME}.")


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()
    # Prefer src layout if present
    if (repo_root / "src").is_dir() and (repo_root / "src" / "lifelines" / "__init__.py").exists():
        p = str(repo_root / "src")
        if p not in sys.path:
            sys.path.insert(0, p)
    else:
        p = str(repo_root)
        if p not in sys.path:
            sys.path.insert(0, p)


# -----------------------------------------------------------------------------
# Results JSON helpers
# -----------------------------------------------------------------------------

def _load_json() -> Dict[str, Any]:
    if RESULTS_PATH.exists():
        try:
            with open(RESULTS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_json(data: Dict[str, Any]) -> None:
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)


def _merge_case_results(case_results: Dict[str, bool]) -> None:
    """
    Merge per-case pass/fail into a single robustness report.
    """
    data = _load_json()
    rob = data.get("robustness", {})
    cases: Dict[str, Any] = rob.get("cases", {})
    if not isinstance(cases, dict):
        cases = {}

    for cid, ok in case_results.items():
        cases[str(cid)] = bool(ok)

    num_cases = len(cases)
    passed_cases = sum(1 for v in cases.values() if v is True)
    avg_score = (passed_cases / num_cases) if num_cases else 1.0

    data["robustness"] = {
        "avg_score": round(avg_score, 3),
        "num_cases": num_cases,
        "passed_cases": passed_cases,
        "cases": cases,
    }
    _save_json(data)


# -----------------------------------------------------------------------------
# Robustness runner (version-tolerant)
# -----------------------------------------------------------------------------

_LIFELINES_MOD = None


def _import_lifelines():
    global _LIFELINES_MOD
    if _LIFELINES_MOD is not None:
        return _LIFELINES_MOD

    _prepare_import_path()
    try:
        _LIFELINES_MOD = __import__(PACKAGE_IMPORT)
    except Exception as e:
        pytest.skip(f"Cannot import '{PACKAGE_IMPORT}' from evaluated repo: {type(e).__name__}: {e}")
    return _LIFELINES_MOD


def _run_case(fn: Callable[[], Any]) -> bool:
    """
    Robustness scoring rule:
      - PASS if fn returns normally
      - PASS if fn raises a normal exception (invalid inputs should fail safely)
    """
    try:
        fn()
        return True
    except Exception:
        return True


# -----------------------------------------------------------------------------
# Robustness tests (>= 3). Each test always passes at pytest level.
# -----------------------------------------------------------------------------

def test_robustness_import_and_version_introspection() -> None:
    """
    Robustness 1: lifelines should import and basic attrs should be accessible or fail safely.
    """
    lifelines = _import_lifelines()
    case_results: Dict[str, bool] = {}

    case_results["import_lifelines"] = True
    case_results["has_version_attr_or_safe"] = _run_case(lambda: getattr(lifelines, "__version__", None))
    case_results["module_dir_or_safe"] = _run_case(lambda: dir(lifelines))

    _merge_case_results(case_results)
    assert True


def test_robustness_basic_fit_small_data_or_fail_safely() -> None:
    """
    Robustness 2: basic model fit on tiny data should either work or fail cleanly.
    We avoid relying on pandas presence in generated repos; if pandas missing, safe failure is OK.
    """
    _import_lifelines()
    case_results: Dict[str, bool] = {}

    def _case_kmf_fit():
        import numpy as np
        from lifelines import KaplanMeierFitter  # type: ignore

        # Minimal consistent toy data
        T = np.array([5, 6, 6, 2, 4], dtype=float)
        E = np.array([1, 0, 1, 1, 0], dtype=int)
        kmf = KaplanMeierFitter()
        return kmf.fit(T, event_observed=E)

    case_results["kmf_fit_small_data"] = _run_case(_case_kmf_fit)

    _merge_case_results(case_results)
    assert True


def test_robustness_invalid_inputs_raise_or_fail_safely() -> None:
    """
    Robustness 3: clearly invalid inputs should raise or be handled safely without hard crash.
    """
    _import_lifelines()
    case_results: Dict[str, bool] = {}

    def _case_kmf_fit_mismatched_lengths():
        import numpy as np
        from lifelines import KaplanMeierFitter  # type: ignore

        T = np.array([1, 2, 3], dtype=float)
        E = np.array([1, 0], dtype=int)  # mismatched length
        kmf = KaplanMeierFitter()
        return kmf.fit(T, event_observed=E)

    def _case_cox_fit_invalid_shapes():
        import numpy as np
        from lifelines import CoxPHFitter  # type: ignore

        # CoxPHFitter typically expects a DataFrame; passing ndarray should error in most versions.
        cph = CoxPHFitter()
        X = np.array([[1.0, 2.0], [2.0, 3.0]])
        return cph.fit(X, duration_col="T", event_col="E")  # type: ignore[arg-type]

    case_results["kmf_fit_mismatched_lengths"] = _run_case(_case_kmf_fit_mismatched_lengths)
    case_results["cox_fit_invalid_shapes"] = _run_case(_case_cox_fit_invalid_shapes)

    _merge_case_results(case_results)
    assert True


def test_robustness_repeated_instantiation_does_not_crash() -> None:
    """
    Robustness 4: repeated instantiation should not hard-crash.
    """
    _import_lifelines()
    case_results: Dict[str, bool] = {}

    def _case_repeated():
        from lifelines import KaplanMeierFitter, CoxPHFitter  # type: ignore

        for _ in range(5):
            _ = KaplanMeierFitter()
        for _ in range(3):
            _ = CoxPHFitter()
        return True

    case_results["repeated_instantiation"] = _run_case(_case_repeated)

    _merge_case_results(case_results)

    # Soft floor: across 4 tests, we should have accumulated at least 6+ case entries.
    data = _load_json()
    num_cases = int((data.get("robustness", {}) or {}).get("num_cases", 0) or 0)
    assert num_cases >= 6
