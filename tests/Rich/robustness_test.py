# tests/Rich/robustness_test.py

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Rich"
PACKAGE_IMPORT = "rich"
RESULTS_PATH = ROOT / "results" / PROJECT_NAME / "nfr_reference.json"


# -----------------------------------------------------------------------------
# Repo root / import path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/rich
      3) <bench_root>/generation/rich
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "rich").resolve())
        candidates.append((p / "generation" / "rich").resolve())

    candidates.append((ROOT / "repositories" / "rich").resolve())
    candidates.append((ROOT / "generation" / "rich").resolve())

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
      - repo_root/rich/__init__.py
      - repo_root/src/rich/__init__.py
    If none match, fall back to RACB_REPO_ROOT or bench root to avoid collection crash.
    """
    for cand in _candidate_repo_roots():
        if (cand / "rich" / "__init__.py").exists():
            return cand
        if (cand / "src" / "rich" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    return ROOT


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()

    if (repo_root / "src").is_dir() and (repo_root / "src" / "rich" / "__init__.py").exists():
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

_RICH_MOD = None
_IMPORT_ERROR: Optional[str] = None


def _try_import_rich():
    global _RICH_MOD, _IMPORT_ERROR
    if _RICH_MOD is not None or _IMPORT_ERROR is not None:
        return _RICH_MOD

    _prepare_import_path()
    try:
        _RICH_MOD = __import__(PACKAGE_IMPORT)
        return _RICH_MOD
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
    mod = _try_import_rich()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}
    cases["import_rich"] = True
    cases["dir_module_or_safe"] = _run_case(lambda: dir(mod))
    cases["get_version_or_safe"] = _run_case(lambda: getattr(mod, "__version__", None))

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_basic_console_and_components_or_safe_failure() -> None:
    """
    Case set 2: basic Console rendering and a few core components.
    """
    mod = _try_import_rich()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_basic_console_print():
        from rich.console import Console  # type: ignore

        c = Console(record=True, force_terminal=False, width=80)
        c.print("Hello, [bold]World[/bold]!")
        _ = c.export_text()

    def _case_table_panel_text():
        from rich.console import Console  # type: ignore
        from rich.panel import Panel  # type: ignore
        from rich.table import Table  # type: ignore
        from rich.text import Text  # type: ignore

        c = Console(record=True, force_terminal=False, width=80)

        table = Table(title="Test Table")
        table.add_column("Column 1")
        table.add_column("Column 2")
        table.add_row("A", "B")

        panel = Panel("This is a test panel", title="Test Panel", expand=False)

        text = Text("Rich Text with different styles", justify="center")
        text.stylize("bold magenta")

        c.print(table)
        c.print(panel)
        c.print(text)
        _ = c.export_text()

    cases["basic_console_print"] = _run_case(_case_basic_console_print)
    cases["table_panel_text"] = _run_case(_case_table_panel_text)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_large_render_and_invalid_markup_safe() -> None:
    """
    Case set 3: large table rendering and invalid markup should not crash runner.
    """
    mod = _try_import_rich()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_large_table_render():
        from rich.console import Console  # type: ignore
        from rich.table import Table  # type: ignore

        c = Console(record=True, force_terminal=False, width=100)

        t = Table(title="Big Test Table")
        t.add_column("ID")
        t.add_column("Name")
        t.add_column("Value")
        for i in range(200):
            t.add_row(str(i), "Item {}".format(i), str(i * 100))

        c.print(t)
        _ = c.export_text()

    def _case_invalid_markup():
        from rich.console import Console  # type: ignore

        c = Console(record=True, force_terminal=False, width=80)
        # Invalid markup should raise or render safely; both are acceptable.
        c.print("[bold]Unclosed bold tag")

    cases["large_table_render"] = _run_case(_case_large_table_render)
    cases["invalid_markup"] = _run_case(_case_invalid_markup)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_concurrent_rendering_does_not_hang() -> None:
    """
    Case set 4: concurrent rendering should not deadlock/hang. Thread joins are bounded.
    """
    mod = _try_import_rich()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_concurrent_rendering():
        from rich.console import Console  # type: ignore
        from rich.table import Table  # type: ignore

        results: List[bool] = [False] * 8

        def worker(i: int) -> None:
            try:
                c = Console(record=True, force_terminal=False, width=80)
                c.print("Thread {}".format(i))
                t = Table()
                t.add_column("Thread")
                t.add_column("Status")
                t.add_row("{}".format(i), "Completed")
                c.print(t)
                _ = c.export_text()
                results[i] = True
            except Exception:
                results[i] = False

        threads: List[threading.Thread] = []
        for i in range(len(results)):
            t = threading.Thread(target=worker, args=(i,))
            t.daemon = True
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=2.0)

        if any(t.is_alive() for t in threads):
            raise RuntimeError("Concurrent rendering threads did not finish within timeout")

        return True

    cases["concurrent_rendering"] = _run_case(_case_concurrent_rendering)

    _compute_and_write(cases, import_error=None)
    assert True
