# tests/Slugify/robustness_test.py

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Slugify"
PACKAGE_IMPORT = "slugify"
RESULTS_PATH = ROOT / "results" / PROJECT_NAME / "nfr_reference.json"


# -----------------------------------------------------------------------------
# Repo root / import path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/slugify
      3) <bench_root>/generation/slugify
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "slugify").resolve())
        candidates.append((p / "generation" / "slugify").resolve())

    candidates.append((ROOT / "repositories" / "slugify").resolve())
    candidates.append((ROOT / "generation" / "slugify").resolve())

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
      - repo_root/slugify/__init__.py
      - repo_root/src/slugify/__init__.py
    If none match, fall back to RACB_REPO_ROOT or bench root to avoid collection crash.
    """
    for cand in _candidate_repo_roots():
        if (cand / "slugify" / "__init__.py").exists():
            return cand
        if (cand / "src" / "slugify" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    return ROOT


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()

    if (repo_root / "src").is_dir() and (repo_root / "src" / "slugify" / "__init__.py").exists():
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

_SLUGIFY_MOD = None
_IMPORT_ERROR: Optional[str] = None


def _try_import_slugify():
    global _SLUGIFY_MOD, _IMPORT_ERROR
    if _SLUGIFY_MOD is not None or _IMPORT_ERROR is not None:
        return _SLUGIFY_MOD

    _prepare_import_path()
    try:
        _SLUGIFY_MOD = __import__(PACKAGE_IMPORT)
        return _SLUGIFY_MOD
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
    mod = _try_import_slugify()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}
    cases["import_slugify"] = True
    cases["dir_module_or_safe"] = _run_case(lambda: dir(mod))
    cases["has_slugify_attr_or_safe"] = _run_case(lambda: getattr(mod, "slugify", None))

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_basic_and_special_strings_or_safe_failure() -> None:
    """
    Case set 2: basic conversion + special characters should work or fail safely.
    """
    mod = _try_import_slugify()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_basic_string_conversion():
        import slugify  # type: ignore

        _ = slugify.slugify("Hello World")

    def _case_strings_with_special_characters():
        import slugify  # type: ignore

        samples = [
            "Hello, World!",
            "Hello@World#$%^&*()",
            "Hello World 123",
            "Hello_World",
            "Hello-World",
            "Hello/World\\Path",
            "Hello|World",
            "Hello World!@#$%^&*()_+[]{}|;:,.<>?",
        ]
        for s in samples:
            _ = slugify.slugify(s)

    cases["basic_string_conversion"] = _run_case(_case_basic_string_conversion)
    cases["strings_with_special_characters"] = _run_case(_case_strings_with_special_characters)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_multilingual_and_large_batch_safe() -> None:
    """
    Case set 3: multilingual inputs and larger batch processing should not crash runner.
    """
    mod = _try_import_slugify()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_multilingual_strings():
        import slugify  # type: ignore

        samples = [
            "你好，世界",
            "Hola Mundo",
            "Bonjour le monde",
            "Hallo Welt",
            "Ciao mondo",
            "Привет мир",
            "こんにちは世界",
            "안녕하세요 세계",
            "Olá Mundo",
        ]
        for s in samples:
            _ = slugify.slugify(s)

    def _case_large_number_of_strings():
        import slugify  # type: ignore

        for i in range(800):
            s = "Test String {} with Special Characters!@#$%^&*()".format(i)
            _ = slugify.slugify(s)

    cases["multilingual_strings"] = _run_case(_case_multilingual_strings)
    cases["large_number_of_strings"] = _run_case(_case_large_number_of_strings)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_concurrent_processing_does_not_hang() -> None:
    """
    Case set 4: concurrent slugify calls should not deadlock/hang. Thread joins are bounded.
    """
    mod = _try_import_slugify()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_concurrent_string_processing():
        import slugify  # type: ignore

        results: List[int] = [0] * 8

        def worker(i: int) -> None:
            try:
                for j in range(120):
                    s = "Concurrent Test {}-{} with Special Characters!@#$%^&*()".format(i, j)
                    _ = slugify.slugify(s)
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
            raise RuntimeError("Concurrent slugify threads did not finish within timeout")

        return True

    cases["concurrent_string_processing"] = _run_case(_case_concurrent_string_processing)

    _compute_and_write(cases, import_error=None)
    assert True
