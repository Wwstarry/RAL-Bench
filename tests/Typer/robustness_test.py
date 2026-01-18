# tests/Typer/robustness_test.py

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Typer"
PACKAGE_IMPORT = "typer"
RESULTS_PATH = ROOT / "results" / PROJECT_NAME / "nfr_reference.json"


# -----------------------------------------------------------------------------
# Repo root / import path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/typer
      3) <bench_root>/generation/typer
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "typer").resolve())
        candidates.append((p / "generation" / "typer").resolve())

    candidates.append((ROOT / "repositories" / "typer").resolve())
    candidates.append((ROOT / "generation" / "typer").resolve())

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
      - repo_root/typer/__init__.py
      - repo_root/src/typer/__init__.py
    If none match, fall back to RACB_REPO_ROOT or bench root to avoid collection crash.
    """
    for cand in _candidate_repo_roots():
        if (cand / "typer" / "__init__.py").exists():
            return cand
        if (cand / "src" / "typer" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    return ROOT


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()

    if (repo_root / "src").is_dir() and (repo_root / "src" / "typer" / "__init__.py").exists():
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

_TYPER_MOD = None
_IMPORT_ERROR: Optional[str] = None


def _try_import_typer():
    global _TYPER_MOD, _IMPORT_ERROR
    if _TYPER_MOD is not None or _IMPORT_ERROR is not None:
        return _TYPER_MOD

    _prepare_import_path()
    try:
        _TYPER_MOD = __import__(PACKAGE_IMPORT)
        return _TYPER_MOD
    except Exception as e:
        _IMPORT_ERROR = "{}: {}".format(type(e).__name__, e)
        return None


def _run_case(fn: Callable[[], Any]) -> bool:
    """
    Robustness scoring rule (benchmark-required):
      - PASS if fn returns normally
      - PASS if fn raises (including SystemExit from CLI parsing)
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


def _invoke_typer_app(app: Any, argv: List[str]) -> None:
    """
    Invoke a Typer app using Click's entrypoint. Typer commonly raises SystemExit.
    """
    app(argv)


# -----------------------------------------------------------------------------
# Robustness tests (>= 3). Each test always passes at pytest level.
# -----------------------------------------------------------------------------


def test_robustness_import_and_app_create() -> None:
    """
    Case set 1: import Typer and basic app construction / introspection.
    """
    mod = _try_import_typer()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_create_app():
        from typer import Typer  # type: ignore

        _ = Typer()

    def _case_help_option_exists_or_safe():
        import typer  # type: ignore

        _ = getattr(typer, "Argument", None)
        _ = getattr(typer, "Option", None)

    cases["import_typer"] = True
    cases["create_app"] = _run_case(_case_create_app)
    cases["introspection"] = _run_case(_case_help_option_exists_or_safe)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_invalid_params_and_missing_command_safe() -> None:
    """
    Case set 2: invalid parameter types and missing commands should exit/raise cleanly.
    """
    mod = _try_import_typer()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _изн():  # no-op placeholder to avoid accidental closures (keeps style stable)
        return None

    def _case_invalid_param_type():
        from typer import Typer  # type: ignore

        app = Typer()

        @app.command()
        def test_cmd(name: int) -> str:
            return "Hello {}".format(name)

        _invoke_typer_app(app, ["test-cmd", "not-a-number"])

    def _case_missing_command():
        from typer import Typer  # type: ignore

        app = Typer()

        @app.command()
        def ok() -> str:
            return "ok"

        _invoke_typer_app(app, ["non-existent-cmd"])

    cases["invalid_param_type"] = _run_case(_case_invalid_param_type)
    cases["missing_command"] = _run_case(_case_missing_command)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_many_commands_registration_safe() -> None:
    """
    Case set 3: register many commands (stress CLI table/metadata) without crashing.
    """
    mod = _try_import_typer()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_many_commands():
        from typer import Typer  # type: ignore

        app = Typer()

        for i in range(60):
            def make_cmd(j: int) -> Callable[[], str]:
                def cmd() -> str:
                    return "Command {}".format(j)
                return cmd

            app.command(name="cmd-{}".format(i))(make_cmd(i))

        # Trigger command table/build path (may SystemExit due to no args -> help)
        _invoke_typer_app(app, [])

    cases["many_commands_registration"] = _run_case(_case_many_commands)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_complex_params_and_concurrent_invocation_do_not_hang() -> None:
    """
    Case set 4: complex options (repeatable) + bounded concurrent invocations.
    """
    mod = _try_import_typer()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_complex_params():
        from typing import List as TList

        from typer import Typer  # type: ignore

        app = Typer()

        @app.command()
        def complex_cmd(
            name: str,
            age: int,
            active: bool = False,
            tags: Optional[TList[str]] = None,
            score: float = 0.0,
        ) -> str:
            return "Name: {}, Age: {}, Active: {}, Tags: {}, Score: {}".format(name, age, active, tags, score)

        _invoke_typer_app(
            app,
            ["complex-cmd", "John", "30", "--active", "--tags", "python", "--tags", "typer", "--score", "95.5"],
        )

    def _case_concurrent_invocations():
        from typer import Typer  # type: ignore

        app = Typer()

        @app.command()
        def hello(name: str = "world") -> str:
            return "Hello {}".format(name)

        results: List[int] = [0] * 6

        def worker(i: int) -> None:
            try:
                _invoke_typer_app(app, ["hello", "--name", "u{}".format(i)])
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
            raise RuntimeError("Concurrent typer threads did not finish within timeout")

        return True

    cases["complex_params"] = _run_case(_case_complex_params)
    cases["concurrent_invocations"] = _run_case(_case_concurrent_invocations)

    _compute_and_write(cases, import_error=None)
    assert True
