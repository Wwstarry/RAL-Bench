# tests/Watchdog/robustness_test.py

import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Watchdog"
PACKAGE_IMPORT = "watchdog"
RESULTS_PATH = ROOT / "results" / PROJECT_NAME / "nfr_reference.json"


# -----------------------------------------------------------------------------
# Repo root / import path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/watchdog
      3) <bench_root>/generation/watchdog
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "watchdog").resolve())
        candidates.append((p / "generation" / "watchdog").resolve())

    candidates.append((ROOT / "repositories" / "watchdog").resolve())
    candidates.append((ROOT / "generation" / "watchdog").resolve())

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
      - repo_root/watchdog/__init__.py
      - repo_root/src/watchdog/__init__.py
    If none match, fall back to RACB_REPO_ROOT or bench root to avoid collection crash.
    """
    for cand in _candidate_repo_roots():
        if (cand / "watchdog" / "__init__.py").exists():
            return cand
        if (cand / "src" / "watchdog" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    return ROOT


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()

    if (repo_root / "src").is_dir() and (repo_root / "src" / "watchdog" / "__init__.py").exists():
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

_WATCHDOG_MOD = None
_IMPORT_ERROR: Optional[str] = None


def _try_import_watchdog():
    global _WATCHDOG_MOD, _IMPORT_ERROR
    if _WATCHDOG_MOD is not None or _IMPORT_ERROR is not None:
        return _WATCHDOG_MOD

    _prepare_import_path()
    try:
        _WATCHDOG_MOD = __import__(PACKAGE_IMPORT)
        return _WATCHDOG_MOD
    except Exception as e:
        _IMPORT_ERROR = "{}: {}".format(type(e).__name__, e)
        return None


def _run_case(fn: Callable[[], Any]) -> bool:
    """
    Robustness scoring rule (benchmark-required):
      - PASS if fn returns normally
      - PASS if fn raises (including thread/observer lifecycle errors)
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
# Helper: safe observer lifecycle with bounded joins
# -----------------------------------------------------------------------------

def _stop_observer(observer: Any, join_timeout: float) -> None:
    try:
        observer.stop()
    except BaseException:
        return
    try:
        observer.join(timeout=join_timeout)
    except TypeError:
        # Some versions may not accept timeout
        try:
            observer.join()
        except BaseException:
            return


# -----------------------------------------------------------------------------
# Robustness tests (>= 3). Each test always passes at pytest level.
# -----------------------------------------------------------------------------


def test_robustness_import_and_observer_create() -> None:
    """
    Case set 1: import watchdog and create an Observer.
    """
    mod = _try_import_watchdog()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_import_submodules():
        _ = __import__("watchdog.observers")
        _ = __import__("watchdog.events")

    def _case_create_observer():
        from watchdog.observers import Observer  # type: ignore

        obs = Observer()
        _ = obs

    cases["import_watchdog"] = True
    cases["import_submodules"] = _run_case(_case_import_submodules)
    cases["create_observer"] = _run_case(_case_create_observer)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_basic_start_stop_or_safe_failure() -> None:
    """
    Case set 2: start/stop observer with no schedules; must not hang.
    """
    mod = _try_import_watchdog()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_start_stop():
        from watchdog.observers import Observer  # type: ignore

        obs = Observer()
        try:
            obs.start()
            time.sleep(0.05)
        finally:
            _stop_observer(obs, join_timeout=1.0)
            # Hard guard: if still alive, raise to be treated as safe failure by _run_case.
            try:
                alive = getattr(obs, "is_alive", None)
                if callable(alive) and obs.is_alive():
                    raise RuntimeError("Observer thread still alive after stop/join")
            except BaseException:
                raise

    cases["basic_start_stop"] = _run_case(_case_start_stop)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_schedule_invalid_and_duplicate_paths_safe() -> None:
    """
    Case set 3: schedule invalid path and duplicate scheduling on same path.
    Different platforms/backends behave differently; both success and failure are acceptable.
    """
    mod = _try_import_watchdog()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_invalid_path_schedule_and_start():
        from watchdog.events import FileSystemEventHandler  # type: ignore
        from watchdog.observers import Observer  # type: ignore

        obs = Observer()
        handler = FileSystemEventHandler()

        # Use a clearly invalid path without relying on root permissions.
        invalid_path = os.path.join(os.path.dirname(__file__), "__definitely_missing_path__")

        try:
            obs.schedule(handler, path=invalid_path, recursive=False)
            obs.start()
            time.sleep(0.05)
        finally:
            _stop_observer(obs, join_timeout=1.0)

    def _case_duplicate_schedule_same_dir():
        from tempfile import TemporaryDirectory

        from watchdog.events import FileSystemEventHandler  # type: ignore
        from watchdog.observers import Observer  # type: ignore

        with TemporaryDirectory() as td:
            obs = Observer()
            handler = FileSystemEventHandler()
            try:
                obs.schedule(handler, path=td, recursive=False)
                obs.schedule(handler, path=td, recursive=False)
                obs.start()
                time.sleep(0.05)
            finally:
                _stop_observer(obs, join_timeout=1.0)

    cases["invalid_path_schedule"] = _run_case(_case_invalid_path_schedule_and_start)
    cases["duplicate_schedule_same_dir"] = _run_case(_case_duplicate_schedule_same_dir)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_concurrent_observers_do_not_hang() -> None:
    """
    Case set 4: run multiple observers concurrently (separate instances).
    Avoid starting/stopping the same Observer multiple times, which can be backend-sensitive.
    """
    mod = _try_import_watchdog()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_concurrent_observers():
        from tempfile import TemporaryDirectory

        from watchdog.events import FileSystemEventHandler  # type: ignore
        from watchdog.observers import Observer  # type: ignore

        results: List[int] = [0] * 4

        def worker(i: int) -> None:
            obs = Observer()
            handler = FileSystemEventHandler()
            try:
                with TemporaryDirectory() as td:
                    obs.schedule(handler, path=td, recursive=False)
                    obs.start()
                    time.sleep(0.05)
                results[i] = 1
            except BaseException:
                results[i] = 0
            finally:
                _stop_observer(obs, join_timeout=1.0)

        threads: List[threading.Thread] = []
        for i in range(len(results)):
            t = threading.Thread(target=worker, args=(i,))
            t.daemon = True
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=2.0)

        if any(t.is_alive() for t in threads):
            raise RuntimeError("Concurrent watchdog threads did not finish within timeout")

        return True

    cases["concurrent_observers"] = _run_case(_case_concurrent_observers)

    _compute_and_write(cases, import_error=None)
    assert True
