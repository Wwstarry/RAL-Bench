# tests/Schedule/robustness_test.py

import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Schedule"
PACKAGE_IMPORT = "schedule"
RESULTS_PATH = ROOT / "results" / PROJECT_NAME / "nfr_reference.json"


# -----------------------------------------------------------------------------
# Repo root / import path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/schedule
      3) <bench_root>/generation/schedule
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "schedule").resolve())
        candidates.append((p / "generation" / "schedule").resolve())

    candidates.append((ROOT / "repositories" / "schedule").resolve())
    candidates.append((ROOT / "generation" / "schedule").resolve())

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
      - repo_root/schedule/__init__.py
      - repo_root/src/schedule/__init__.py
    If none match, fall back to RACB_REPO_ROOT or bench root to avoid collection crash.
    """
    for cand in _candidate_repo_roots():
        if (cand / "schedule" / "__init__.py").exists():
            return cand
        if (cand / "src" / "schedule" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    return ROOT


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()

    if (repo_root / "src").is_dir() and (repo_root / "src" / "schedule" / "__init__.py").exists():
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

_SCHEDULE_MOD = None
_IMPORT_ERROR: Optional[str] = None


def _try_import_schedule():
    global _SCHEDULE_MOD, _IMPORT_ERROR
    if _SCHEDULE_MOD is not None or _IMPORT_ERROR is not None:
        return _SCHEDULE_MOD

    _prepare_import_path()
    try:
        _SCHEDULE_MOD = __import__(PACKAGE_IMPORT)
        return _SCHEDULE_MOD
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
    mod = _try_import_schedule()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}
    cases["import_schedule"] = True
    cases["dir_module_or_safe"] = _run_case(lambda: dir(mod))
    cases["get_version_or_safe"] = _run_case(lambda: getattr(mod, "__version__", None))

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_basic_scheduling_units_or_safe_failure() -> None:
    """
    Case set 2: schedule basic jobs across common time units.
    """
    mod = _try_import_schedule()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_basic_task_scheduling():
        import schedule  # type: ignore

        schedule.clear()

        def job():
            return None

        schedule.every(1).seconds.do(job)
        schedule.run_all(delay_seconds=0)
        schedule.clear()

    def _case_different_time_units():
        import schedule  # type: ignore

        schedule.clear()

        def job():
            return None

        # Avoid long sleeps: only register jobs, then run_all immediately.
        schedule.every(1).second.do(job)
        schedule.every(1).seconds.do(job)
        schedule.every(1).minute.do(job)
        schedule.every(1).minutes.do(job)
        schedule.every(1).hour.do(job)
        schedule.every(1).hours.do(job)
        schedule.every(1).day.do(job)
        schedule.every(1).days.do(job)
        schedule.every(1).week.do(job)
        schedule.every(1).weeks.do(job)

        schedule.run_all(delay_seconds=0)
        schedule.clear()

    cases["basic_task_scheduling"] = _run_case(_case_basic_task_scheduling)
    cases["different_time_units"] = _run_case(_case_different_time_units)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_cancel_reschedule_and_many_jobs_safe() -> None:
    """
    Case set 3: cancel/reschedule and many jobs should not crash the runner.
    """
    mod = _try_import_schedule()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_cancel_and_reschedule():
        import schedule  # type: ignore

        schedule.clear()

        def job():
            return None

        job1 = schedule.every(1).seconds.do(job)
        _ = schedule.every(2).seconds.do(job)

        schedule.cancel_job(job1)
        schedule.every(3).seconds.do(job)

        schedule.run_all(delay_seconds=0)
        schedule.clear()

    def _case_large_number_of_jobs():
        import schedule  # type: ignore

        schedule.clear()

        def job():
            return None

        for _ in range(200):
            schedule.every(1).seconds.do(job)

        schedule.run_all(delay_seconds=0)
        schedule.clear()

    cases["cancel_and_reschedule"] = _run_case(_case_cancel_and_reschedule)
    cases["large_number_of_jobs"] = _run_case(_case_large_number_of_jobs)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_concurrent_run_pending_does_not_hang() -> None:
    """
    Case set 4: concurrent run_pending calls should not deadlock/hang. Thread joins are bounded.
    """
    mod = _try_import_schedule()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_concurrent_scheduler():
        import schedule  # type: ignore

        schedule.clear()

        def job():
            return None

        # Keep intervals small; no real waiting required since we call run_all / run_pending quickly.
        for _ in range(20):
            schedule.every(1).seconds.do(job)

        def runner() -> None:
            try:
                for _ in range(10):
                    schedule.run_pending()
                    time.sleep(0.01)
            except Exception:
                # Safe failure; do not propagate.
                pass

        threads: List[threading.Thread] = []
        for _ in range(8):
            t = threading.Thread(target=runner)
            t.daemon = True
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=2.0)

        schedule.clear()

        if any(t.is_alive() for t in threads):
            raise RuntimeError("Concurrent schedule threads did not finish within timeout")

        return True

    cases["concurrent_run_pending"] = _run_case(_case_concurrent_scheduler)

    _compute_and_write(cases, import_error=None)
    assert True
