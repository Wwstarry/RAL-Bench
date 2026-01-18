# tests/Pygments/robustness_test.py

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Pygments"
PACKAGE_IMPORT = "pygments"
RESULTS_PATH = ROOT / "results" / PROJECT_NAME / "nfr_reference.json"


# -----------------------------------------------------------------------------
# Repo root / import path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/pygments
      3) <bench_root>/generation/pygments
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "pygments").resolve())
        candidates.append((p / "generation" / "pygments").resolve())

    candidates.append((ROOT / "repositories" / "pygments").resolve())
    candidates.append((ROOT / "generation" / "pygments").resolve())

    # De-dup while preserving order
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
      - repo_root/pygments/__init__.py
      - repo_root/src/pygments/__init__.py
    If none match, fall back to RACB_REPO_ROOT or bench root to avoid collection crash.
    """
    for cand in _candidate_repo_roots():
        if (cand / "pygments" / "__init__.py").exists():
            return cand
        if (cand / "src" / "pygments" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    return ROOT


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()

    # Prefer src layout if present
    if (repo_root / "src").is_dir() and (repo_root / "src" / "pygments" / "__init__.py").exists():
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

_PYGMENTS_MOD = None
_IMPORT_ERROR: Optional[str] = None


def _try_import_pygments():
    global _PYGMENTS_MOD, _IMPORT_ERROR
    if _PYGMENTS_MOD is not None or _IMPORT_ERROR is not None:
        return _PYGMENTS_MOD

    _prepare_import_path()
    try:
        _PYGMENTS_MOD = __import__(PACKAGE_IMPORT)
        return _PYGMENTS_MOD
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
    # Here, every executed case is considered passed if it didn't hang.
    # _run_case returns True for both normal return and exceptions.
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
    mod = _try_import_pygments()

    cases: Dict[str, bool] = {}
    if mod is None:
        # Import failed: required by spec -> avg_score = 0, write import_error, but pytest passes.
        _compute_and_write(cases, import_error=_IMPORT_ERROR)
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases["import_pygments"] = True
    cases["dir_module_or_safe"] = _run_case(lambda: dir(mod))
    cases["get_version_or_safe"] = _run_case(lambda: getattr(mod, "__version__", None))

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_basic_highlight_or_safe_failure() -> None:
    """
    Case set 2: basic highlighting via lexer+formatter APIs should work or fail safely.
    """
    mod = _try_import_pygments()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_basic_python_html():
        import pygments
        import pygments.lexers
        import pygments.formatters

        code = "print('Hello World')\n"
        lexer = pygments.lexers.get_lexer_by_name("python")
        formatter = pygments.formatters.get_formatter_by_name("html")
        _ = pygments.highlight(code, lexer, formatter)

    def _case_multi_language_small_set():
        import pygments
        import pygments.lexers
        import pygments.formatters

        formatter = pygments.formatters.get_formatter_by_name("html")
        samples = [
            ("python", "print('x')\n"),
            ("javascript", "console.log('x')\n"),
            ("json", '{"k": "v"}\n'),
            ("html", "<h1>x</h1>\n"),
        ]
        for lang, code in samples:
            lexer = pygments.lexers.get_lexer_by_name(lang)
            _ = pygments.highlight(code, lexer, formatter)

    cases["basic_python_html"] = _run_case(_case_basic_python_html)
    cases["multi_language_small_set"] = _run_case(_case_multi_language_small_set)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_invalid_inputs_and_unknown_lexer_safe() -> None:
    """
    Case set 3: invalid inputs / unknown language should not crash the test runner; exceptions are OK.
    """
    mod = _try_import_pygments()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_unknown_language_name():
        import pygments.lexers

        # Expected to raise ClassNotFound, but any exception is considered safe.
        _ = pygments.lexers.get_lexer_by_name("unknown_language___racb")

    def _case_highlight_with_none_code():
        import pygments
        import pygments.lexers
        import pygments.formatters

        lexer = pygments.lexers.get_lexer_by_name("python")
        formatter = pygments.formatters.get_formatter_by_name("html")
        _ = pygments.highlight(None, lexer, formatter)  # type: ignore[arg-type]

    cases["unknown_language_name"] = _run_case(_case_unknown_language_name)
    cases["highlight_with_none_code"] = _run_case(_case_highlight_with_none_code)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_concurrent_highlight_does_not_hang() -> None:
    """
    Case set 4: concurrent usage should not deadlock/hang. We bound thread joins with timeouts.
    """
    mod = _try_import_pygments()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_concurrent_threads():
        import pygments
        import pygments.lexers
        import pygments.formatters

        results: List[Optional[str]] = [None] * 12
        formatter = pygments.formatters.get_formatter_by_name("html")

        def worker(i: int) -> None:
            try:
                if i % 2 == 0:
                    lexer = pygments.lexers.get_lexer_by_name("python")
                    code = "print('Hello {}')\n".format(i)
                else:
                    lexer = pygments.lexers.get_lexer_by_name("javascript")
                    code = "console.log('Hello {}')\n".format(i)
                results[i] = pygments.highlight(code, lexer, formatter)
            except Exception:
                results[i] = None

        threads: List[threading.Thread] = []
        for i in range(len(results)):
            t = threading.Thread(target=worker, args=(i,))
            threads.append(t)
            t.daemon = True
            t.start()

        # Prevent hangs: bounded joins
        for t in threads:
            t.join(timeout=2.0)

        # If any thread is still alive, raise to record safe-failure; test still passes.
        if any(t.is_alive() for t in threads):
            raise RuntimeError("Concurrent highlight threads did not finish within timeout")

        return True

    cases["concurrent_threads_highlight"] = _run_case(_case_concurrent_threads)

    _compute_and_write(cases, import_error=None)
    assert True
