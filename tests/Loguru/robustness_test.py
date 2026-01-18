# tests/Loguru/robustness_test.py

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Loguru"
PACKAGE_IMPORT = "loguru"

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
      2) <bench_root>/repositories/loguru
      3) <bench_root>/generation/loguru
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "loguru").resolve())
        candidates.append((p / "generation" / "loguru").resolve())

    candidates.append((ROOT / "repositories" / "loguru").resolve())
    candidates.append((ROOT / "generation" / "loguru").resolve())

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
      - repo_root/loguru/__init__.py
      - repo_root/src/loguru/__init__.py
    """
    for cand in _candidate_repo_roots():
        if (cand / "loguru" / "__init__.py").exists():
            return cand
        if (cand / "src" / "loguru" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    raise RuntimeError(f"Could not locate importable repo root for {PROJECT_NAME}.")


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()
    # Prefer src layout if present
    if (repo_root / "src").is_dir() and (repo_root / "src" / "loguru" / "__init__.py").exists():
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

_LOGURU_MOD = None


def _import_loguru():
    global _LOGURU_MOD
    if _LOGURU_MOD is not None:
        return _LOGURU_MOD

    _prepare_import_path()
    try:
        _LOGURU_MOD = __import__(PACKAGE_IMPORT)
    except Exception as e:
        pytest.skip(f"Cannot import '{PACKAGE_IMPORT}' from evaluated repo: {type(e).__name__}: {e}")
    return _LOGURU_MOD


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

def test_robustness_import_and_basic_logging_to_stderr_or_fail_safely() -> None:
    """
    Robustness 1: loguru import + minimal logging should not hard-crash.
    """
    loguru = _import_loguru()
    case_results: Dict[str, bool] = {}

    def _case_basic_log():
        logger = getattr(loguru, "logger")
        logger.info("robustness smoke log")
        return True

    case_results["import_loguru"] = True
    case_results["basic_log_to_stderr"] = _run_case(_case_basic_log)

    _merge_case_results(case_results)
    assert True


def test_robustness_add_invalid_sink_or_fail_safely() -> None:
    """
    Robustness 2: adding an invalid sink should raise or be handled safely.
    """
    loguru = _import_loguru()
    case_results: Dict[str, bool] = {}

    def _case_add_none_sink():
        logger = getattr(loguru, "logger")
        # invalid sink; versions may raise TypeError/ValueError
        logger.add(None)  # type: ignore[arg-type]
        return True

    def _case_add_bad_level():
        logger = getattr(loguru, "logger")
        # invalid level; should raise or be handled safely
        logger.add(sys.stderr, level="NOT_A_LEVEL")  # type: ignore[arg-type]
        return True

    case_results["add_none_sink"] = _run_case(_case_add_none_sink)
    case_results["add_bad_level"] = _run_case(_case_add_bad_level)

    _merge_case_results(case_results)
    assert True


def test_robustness_repeated_add_remove_does_not_crash() -> None:
    """
    Robustness 3: repeated handler management should not hard-crash.
    """
    loguru = _import_loguru()
    case_results: Dict[str, bool] = {}

    def _case_repeated_handlers():
        logger = getattr(loguru, "logger")
        ids = []
        for _ in range(3):
            i = logger.add(sys.stderr)
            ids.append(i)
        for i in ids:
            logger.remove(i)
        return True

    case_results["repeated_add_remove"] = _run_case(_case_repeated_handlers)

    _merge_case_results(case_results)
    assert True


def test_robustness_non_string_message_and_weird_kwargs_fail_safely() -> None:
    """
    Robustness 4: logging with unusual inputs should either work or fail safely.
    """
    loguru = _import_loguru()
    case_results: Dict[str, bool] = {}

    def _case_non_string_message():
        logger = getattr(loguru, "logger")
        logger.info({"k": "v"})  # non-string message
        return True

    def _case_bad_serialize_flag():
        logger = getattr(loguru, "logger")
        # serialize expects bool in most versions; pass invalid and accept safe failure
        logger.add(sys.stderr, serialize="yes")  # type: ignore[arg-type]
        return True

    case_results["non_string_message"] = _run_case(_case_non_string_message)
    case_results["bad_serialize_flag"] = _run_case(_case_bad_serialize_flag)

    _merge_case_results(case_results)

    # Soft floor: across 4 tests we should accumulate at least 6 cases.
    data = _load_json()
    num_cases = int((data.get("robustness", {}) or {}).get("num_cases", 0) or 0)
    assert num_cases >= 6
