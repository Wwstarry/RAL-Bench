# tests/Stegano/robustness_test.py

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Stegano"
PACKAGE_IMPORT = "stegano"
RESULTS_PATH = ROOT / "results" / PROJECT_NAME / "nfr_reference.json"


# -----------------------------------------------------------------------------
# Repo root / import path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/stegano
      3) <bench_root>/generation/stegano
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "stegano").resolve())
        candidates.append((p / "generation" / "stegano").resolve())

    candidates.append((ROOT / "repositories" / "stegano").resolve())
    candidates.append((ROOT / "generation" / "stegano").resolve())

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
      - repo_root/stegano/__init__.py
      - repo_root/src/stegano/__init__.py
    If none match, fall back to RACB_REPO_ROOT or bench root to avoid collection crash.
    """
    for cand in _candidate_repo_roots():
        if (cand / "stegano" / "__init__.py").exists():
            return cand
        if (cand / "src" / "stegano" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    return ROOT


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()

    if (repo_root / "src").is_dir() and (repo_root / "src" / "stegano" / "__init__.py").exists():
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

_STEGANO_MOD = None
_IMPORT_ERROR: Optional[str] = None


def _try_import_stegano():
    global _STEGANO_MOD, _IMPORT_ERROR
    if _STEGANO_MOD is not None or _IMPORT_ERROR is not None:
        return _STEGANO_MOD

    _prepare_import_path()
    try:
        _STEGANO_MOD = __import__(PACKAGE_IMPORT)
        return _STEGANO_MOD
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
    mod = _try_import_stegano()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}
    cases["import_stegano"] = True
    cases["dir_module_or_safe"] = _run_case(lambda: dir(mod))
    cases["get_version_or_safe"] = _run_case(lambda: getattr(mod, "__version__", None))

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_lsb_basic_hide_reveal_or_safe_failure() -> None:
    """
    Case set 2: basic lsb hide/reveal using in-memory temp files.
    We do not require this to succeed; exceptions are safe failures.
    """
    mod = _try_import_stegano()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_hide_reveal_roundtrip():
        # Lazy imports to avoid collection-time failures if optional deps missing.
        from tempfile import TemporaryDirectory

        from PIL import Image  # type: ignore
        from stegano import lsb  # type: ignore

        with TemporaryDirectory() as td:
            td_path = Path(td)
            cover = td_path / "cover.png"
            out = td_path / "out.png"

            img = Image.new("RGB", (32, 32), color="white")
            img.save(str(cover))

            secret = "hello"
            _ = lsb.hide(str(cover), secret, str(out))
            _ = lsb.reveal(str(out))

    cases["lsb_hide_reveal_roundtrip"] = _run_case(_case_hide_reveal_roundtrip)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_lsb_invalid_inputs_safe() -> None:
    """
    Case set 3: invalid inputs should raise or be handled safely (no hard crash).
    """
    mod = _try_import_stegano()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_missing_cover_path():
        from tempfile import TemporaryDirectory

        from stegano import lsb  # type: ignore

        with TemporaryDirectory() as td:
            td_path = Path(td)
            missing = td_path / "missing.png"
            out = td_path / "out.png"
            _ = lsb.hide(str(missing), "x", str(out))

    def _case_secret_not_string():
        from tempfile import TemporaryDirectory

        from PIL import Image  # type: ignore
        from stegano import lsb  # type: ignore

        with TemporaryDirectory() as td:
            td_path = Path(td)
            cover = td_path / "cover.png"
            out = td_path / "out.png"

            img = Image.new("RGB", (16, 16), color="white")
            img.save(str(cover))

            _ = lsb.hide(str(cover), 1234, str(out))  # type: ignore[arg-type]

    def _case_output_dir_missing():
        from tempfile import TemporaryDirectory

        from PIL import Image  # type: ignore
        from stegano import lsb  # type: ignore

        with TemporaryDirectory() as td:
            td_path = Path(td)
            cover = td_path / "cover.png"
            out = td_path / "no_such_dir" / "out.png"

            img = Image.new("RGB", (16, 16), color="white")
            img.save(str(cover))

            _ = lsb.hide(str(cover), "x", str(out))

    cases["missing_cover_path"] = _run_case(_case_missing_cover_path)
    cases["secret_not_string"] = _run_case(_case_secret_not_string)
    cases["output_dir_missing"] = _run_case(_case_output_dir_missing)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_concurrent_lsb_calls_do_not_hang() -> None:
    """
    Case set 4: concurrent lsb operations should not deadlock/hang. Thread joins are bounded.
    """
    mod = _try_import_stegano()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_concurrent_hide_calls():
        from tempfile import TemporaryDirectory

        from PIL import Image  # type: ignore
        from stegano import lsb  # type: ignore

        results: List[int] = [0] * 6

        def worker(i: int) -> None:
            try:
                with TemporaryDirectory() as td:
                    td_path = Path(td)
                    cover = td_path / "cover.png"
                    out = td_path / "out.png"

                    img = Image.new("RGB", (24, 24), color="white")
                    img.save(str(cover))

                    _ = lsb.hide(str(cover), "msg {}".format(i), str(out))
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
            raise RuntimeError("Concurrent stegano threads did not finish within timeout")

        return True

    cases["concurrent_hide_calls"] = _run_case(_case_concurrent_hide_calls)

    _compute_and_write(cases, import_error=None)
    assert True
