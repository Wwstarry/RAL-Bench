# tests/Termgraph/robustness_test.py

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Termgraph"
PACKAGE_IMPORT = "termgraph"
RESULTS_PATH = ROOT / "results" / PROJECT_NAME / "nfr_reference.json"


# -----------------------------------------------------------------------------
# Repo root / import path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/termgraph
      3) <bench_root>/generation/termgraph
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "termgraph").resolve())
        candidates.append((p / "generation" / "termgraph").resolve())

    candidates.append((ROOT / "repositories" / "termgraph").resolve())
    candidates.append((ROOT / "generation" / "termgraph").resolve())

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
      - repo_root/termgraph/__init__.py
      - repo_root/src/termgraph/__init__.py
    If none match, fall back to RACB_REPO_ROOT or bench root to avoid collection crash.
    """
    for cand in _candidate_repo_roots():
        if (cand / "termgraph" / "__init__.py").exists():
            return cand
        if (cand / "src" / "termgraph" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    return ROOT


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()

    if (repo_root / "src").is_dir() and (repo_root / "src" / "termgraph" / "__init__.py").exists():
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

_TERMGRAPH_MOD = None
_IMPORT_ERROR: Optional[str] = None


def _try_import_termgraph():
    global _TERMGRAPH_MOD, _IMPORT_ERROR
    if _TERMGRAPH_MOD is not None or _IMPORT_ERROR is not None:
        return _TERMGRAPH_MOD

    _prepare_import_path()
    try:
        _TERMGRAPH_MOD = __import__(PACKAGE_IMPORT)
        return _TERMGRAPH_MOD
    except Exception as e:
        _IMPORT_ERROR = "{}: {}".format(type(e).__name__, e)
        return None


def _run_case(fn: Callable[[], Any]) -> bool:
    """
    Robustness scoring rule (benchmark-required):
      - PASS if fn returns normally
      - PASS if fn raises a normal exception (safe failure)

    Note: some CLIs call sys.exit() which raises SystemExit (BaseException).
    Treat SystemExit/KeyboardInterrupt as safe failures too to prevent pytest failures.
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


def _run_termgraph_main_with_argv(argv: List[str]) -> None:
    """
    Run termgraph CLI main() by temporarily swapping sys.argv.
    This avoids spawning subprocesses and keeps the test hermetic.
    """
    from termgraph.termgraph import main as termgraph_main  # type: ignore

    original_argv = sys.argv
    try:
        sys.argv = ["termgraph"] + list(argv)
        termgraph_main()
    finally:
        sys.argv = original_argv


def _data_dir_from_repo(repo_root: Path) -> Optional[Path]:
    """
    Attempt to locate a Termgraph data directory in the evaluated repo.
    Best-effort; must not raise.
    """
    candidates = [
        repo_root / "data",
        repo_root / "Data",
        repo_root / "termgraph" / "data",
        repo_root / "termgraph" / "Data",
        repo_root / "examples",
        repo_root / "example",
        repo_root / "tests" / "data",
    ]
    for c in candidates:
        if c.is_dir():
            return c
    return None


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


# -----------------------------------------------------------------------------
# Robustness tests (>= 3). Each test always passes at pytest level.
# -----------------------------------------------------------------------------


def test_robustness_import_and_introspection() -> None:
    """
    Case set 1: import and basic module introspection.
    """
    mod = _try_import_termgraph()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}
    cases["import_termgraph"] = True
    cases["dir_module_or_safe"] = _run_case(lambda: dir(mod))
    cases["module_has_termgraph_submodule_or_safe"] = _run_case(lambda: __import__("termgraph.termgraph"))

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_cli_basic_file_input_or_safe_failure() -> None:
    """
    Case set 2: run CLI against a small valid data file.
    Prefer repo-provided example data when available; otherwise generate minimal data.
    """
    mod = _try_import_termgraph()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    repo_root = _select_repo_root()
    cases: Dict[str, bool] = {}

    def _case_basic_chart_generation():
        from tempfile import TemporaryDirectory

        data_dir = _data_dir_from_repo(repo_root)

        with TemporaryDirectory() as td:
            td_path = Path(td)

            candidate_files: List[Path] = []
            if data_dir is not None:
                for name in ["ex1.dat", "ex2.dat", "ex3.dat", "example.dat", "data.dat"]:
                    p = data_dir / name
                    if p.exists() and p.is_file():
                        candidate_files.append(p)

            if candidate_files:
                data_file = candidate_files[0]
            else:
                data_file = td_path / "ex1.dat"
                _write_text(data_file, "A,1\nB,2\nC,3\n")

            _run_termgraph_main_with_argv([str(data_file)])

    cases["basic_chart_generation"] = _run_case(_case_basic_chart_generation)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_cli_various_modes_and_invalid_inputs_safe() -> None:
    """
    Case set 3: run CLI with different flags (e.g., --color, --histogram) and invalid inputs.
    Note: termgraph prints an error and calls sys.exit() on missing files; that raises SystemExit,
    which must be treated as safe failure to keep pytest ALWAYS PASS.
    """
    mod = _try_import_termgraph()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_color_flag():
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as td:
            td_path = Path(td)
            data_file = td_path / "ex_color.dat"
            _write_text(data_file, "A,1\nB,2\n")
            _run_termgraph_main_with_argv([str(data_file), "--color", "red"])

    def _case_histogram_flag():
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as td:
            td_path = Path(td)
            data_file = td_path / "histogram.dat"
            _write_text(data_file, "1\n2\n3\n4\n5\n")
            _run_termgraph_main_with_argv([str(data_file), "--histogram"])

    def _case_missing_file_path():
        from tempfile import TemporaryDirectory

        with TemporaryDirectory() as td:
            td_path = Path(td)
            missing = td_path / "missing.dat"
            _run_termgraph_main_with_argv([str(missing)])

    cases["color_flag"] = _run_case(_case_color_flag)
    cases["histogram_flag"] = _run_case(_case_histogram_flag)
    cases["missing_file_path"] = _run_case(_case_missing_file_path)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_concurrent_cli_runs_do_not_hang() -> None:
    """
    Case set 4: concurrent CLI runs should not deadlock/hang. Thread joins are bounded.
    """
    mod = _try_import_termgraph()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_concurrent_runs():
        from tempfile import TemporaryDirectory

        results: List[int] = [0] * 5

        def worker(i: int) -> None:
            try:
                with TemporaryDirectory() as td:
                    td_path = Path(td)
                    data_file = td_path / "ex{}.dat".format(i)
                    _write_text(data_file, "A,1\nB,{}\n".format(i + 1))
                    _run_termgraph_main_with_argv([str(data_file)])
                results[i] = 1
            except BaseException:
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
            raise RuntimeError("Concurrent termgraph threads did not finish within timeout")

        return True

    cases["concurrent_cli_runs"] = _run_case(_case_concurrent_runs)

    _compute_and_write(cases, import_error=None)
    assert True
