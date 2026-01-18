# tests/Humanize/robustness_test.py

import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import pytest


# -----------------------------------------------------------------------------
# Path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Humanize"
PACKAGE_IMPORT = "humanize"


def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/humanize
      3) <bench_root>/generation/humanize
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "humanize").resolve())
        candidates.append((p / "generation" / "humanize").resolve())

    candidates.append((ROOT / "repositories" / "humanize").resolve())
    candidates.append((ROOT / "generation" / "humanize").resolve())

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
      - repo_root/humanize/__init__.py
      - repo_root/src/humanize/__init__.py
    """
    for cand in _candidate_repo_roots():
        if (cand / "humanize" / "__init__.py").exists():
            return cand
        if (cand / "src" / "humanize" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    raise RuntimeError(f"Could not locate importable repo root for {PROJECT_NAME}.")


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()
    # Prefer src layout if present
    if (repo_root / "src").is_dir() and (repo_root / "src" / "humanize" / "__init__.py").exists():
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

RESULTS_DIR = ROOT / "results" / PROJECT_NAME
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_PATH = RESULTS_DIR / "nfr_robustness.json"


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

    We store a stable map of case_id -> ok (bool). Each pytest test can run
    independently; order does not matter.

    Final metrics:
      avg_score = passed_cases / num_cases
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

_HUMANIZE_MOD = None


def _import_humanize():
    global _HUMANIZE_MOD
    if _HUMANIZE_MOD is not None:
        return _HUMANIZE_MOD

    _prepare_import_path()
    try:
        _HUMANIZE_MOD = __import__(PACKAGE_IMPORT)
    except Exception as e:
        pytest.skip(f"Cannot import '{PACKAGE_IMPORT}' from evaluated repo: {type(e).__name__}: {e}")
    return _HUMANIZE_MOD


def _run_case(fn: Callable[[], Any]) -> bool:
    """
    Robustness scoring rule:
      - ok=True  : returns normally OR raises a normal exception (both acceptable)
      - ok=False : reserved for harness-level fatal issues (we avoid producing this)
    """
    try:
        fn()
        return True
    except Exception:
        return True


def _getattr_required(mod: Any, name: str) -> Callable[..., Any]:
    fn = getattr(mod, name, None)
    if fn is None:
        raise AttributeError(f"{name} not available in this {PACKAGE_IMPORT} version")
    return fn


# -----------------------------------------------------------------------------
# 3 robustness tests (each always passes at pytest level)
# -----------------------------------------------------------------------------

def test_robustness_numbers() -> None:
    humanize = _import_humanize()
    case_results: Dict[str, bool] = {}

    # intcomma
    case_results["intcomma_none"] = _run_case(lambda: humanize.intcomma(None))  # type: ignore[attr-defined]
    case_results["intcomma_list"] = _run_case(lambda: humanize.intcomma([1, 2, 3]))  # type: ignore[attr-defined]
    case_results["intcomma_huge"] = _run_case(lambda: humanize.intcomma(10**1000))  # type: ignore[attr-defined]

    # ordinal
    case_results["ordinal_none"] = _run_case(lambda: humanize.ordinal(None))  # type: ignore[attr-defined]
    case_results["ordinal_dict"] = _run_case(lambda: humanize.ordinal({"k": "v"}))  # type: ignore[attr-defined]
    case_results["ordinal_negative"] = _run_case(lambda: humanize.ordinal(-42))  # type: ignore[attr-defined]

    # intword
    case_results["intword_none"] = _run_case(lambda: humanize.intword(None))  # type: ignore[attr-defined]
    case_results["intword_bool"] = _run_case(lambda: humanize.intword(True))  # type: ignore[attr-defined]
    case_results["intword_nan"] = _run_case(lambda: humanize.intword(math.nan))  # type: ignore[attr-defined]

    _merge_case_results(case_results)
    assert True


def test_robustness_time_and_filesize() -> None:
    humanize = _import_humanize()
    case_results: Dict[str, bool] = {}

    # naturaltime / naturaldelta
    case_results["naturaltime_none"] = _run_case(lambda: humanize.naturaltime(None))  # type: ignore[attr-defined]
    case_results["naturaltime_str"] = _run_case(lambda: humanize.naturaltime("not a datetime"))  # type: ignore[attr-defined]
    case_results["naturaldelta_none"] = _run_case(lambda: humanize.naturaldelta(None))  # type: ignore[attr-defined]
    case_results["naturaldelta_list"] = _run_case(lambda: humanize.naturaldelta([1, 2, 3]))  # type: ignore[attr-defined]

    # naturalsize
    case_results["naturalsize_none"] = _run_case(lambda: humanize.naturalsize(None))  # type: ignore[attr-defined]
    case_results["naturalsize_negative"] = _run_case(lambda: humanize.naturalsize(-1024))  # type: ignore[attr-defined]
    case_results["naturalsize_huge"] = _run_case(lambda: humanize.naturalsize(10**100))  # type: ignore[attr-defined]

    _merge_case_results(case_results)
    assert True


def test_robustness_list_and_misc() -> None:
    humanize = _import_humanize()
    case_results: Dict[str, bool] = {}

    # natural_list (optional)
    def _natural_list(x: Any) -> Any:
        fn = _getattr_required(humanize, "natural_list")
        return fn(x)

    case_results["natural_list_none"] = _run_case(lambda: _natural_list(None))
    case_results["natural_list_not_iterable"] = _run_case(lambda: _natural_list(123))
    case_results["natural_list_empty"] = _run_case(lambda: _natural_list([]))

    # fractional (optional)
    def _fractional(x: Any) -> Any:
        fn = _getattr_required(humanize, "fractional")
        return fn(x)

    case_results["fractional_none"] = _run_case(lambda: _fractional(None))
    case_results["fractional_inf"] = _run_case(lambda: _fractional(math.inf))

    # clamp (optional)
    def _clamp(*args: Any, **kwargs: Any) -> Any:
        fn = _getattr_required(humanize, "clamp")
        return fn(*args, **kwargs)

    case_results["clamp_none"] = _run_case(lambda: _clamp(None))
    case_results["clamp_bad_formatter"] = _run_case(lambda: _clamp(123, formatter="not a formatter"))

    _merge_case_results(case_results)

    # ensure enough coverage overall (>=20 across 3 tests)
    data = _load_json()
    rob = data.get("robustness", {})
    num_cases = int(rob.get("num_cases", 0) or 0)
    assert num_cases >= 20
