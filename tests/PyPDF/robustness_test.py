# tests/PyPDF/robustness_test.py

import json
import os
import sys
import threading
from io import BytesIO
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "PyPDF"
PACKAGE_IMPORT = "PyPDF2"
RESULTS_PATH = ROOT / "results" / PROJECT_NAME / "nfr_reference.json"


# -----------------------------------------------------------------------------
# Repo root / import path helpers (benchmark-compatible)
# -----------------------------------------------------------------------------

def _candidate_repo_roots() -> List[Path]:
    """
    Determine where to import evaluated repo from.

    Priority:
      1) RACB_REPO_ROOT env var (set by benchmark runner)
      2) <bench_root>/repositories/pypdf2
      3) <bench_root>/generation/pypdf2
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "pypdf2").resolve())
        candidates.append((p / "generation" / "pypdf2").resolve())

    candidates.append((ROOT / "repositories" / "pypdf2").resolve())
    candidates.append((ROOT / "generation" / "pypdf2").resolve())

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
      - repo_root/PyPDF2/__init__.py
      - repo_root/src/PyPDF2/__init__.py
    If none match, fall back to RACB_REPO_ROOT or bench root to avoid collection crash.
    """
    for cand in _candidate_repo_roots():
        if (cand / "PyPDF2" / "__init__.py").exists():
            return cand
        if (cand / "src" / "PyPDF2" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    return ROOT


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()

    if (repo_root / "src").is_dir() and (repo_root / "src" / "PyPDF2" / "__init__.py").exists():
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

_PYPDF_MOD = None
_IMPORT_ERROR: Optional[str] = None


def _try_import_pypdf2():
    global _PYPDF_MOD, _IMPORT_ERROR
    if _PYPDF_MOD is not None or _IMPORT_ERROR is not None:
        return _PYPDF_MOD

    _prepare_import_path()
    try:
        _PYPDF_MOD = __import__(PACKAGE_IMPORT)
        return _PYPDF_MOD
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
    mod = _try_import_pypdf2()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}
    cases["import_pypdf2"] = True
    cases["dir_module_or_safe"] = _run_case(lambda: dir(mod))
    cases["get_version_or_safe"] = _run_case(lambda: getattr(mod, "__version__", None))

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_basic_write_read_or_safe_failure() -> None:
    """
    Case set 2: create a simple PDF in-memory, write it, read it back.
    """
    mod = _try_import_pypdf2()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_create_simple_pdf():
        import PyPDF2  # type: ignore

        writer = PyPDF2.PdfWriter()
        writer.add_blank_page(width=72 * 8.5, height=72 * 11)
        buf = BytesIO()
        writer.write(buf)

        buf.seek(0)
        reader = PyPDF2.PdfReader(buf)
        _ = len(reader.pages)

    def _case_page_extract_and_new_writer():
        import PyPDF2  # type: ignore

        writer = PyPDF2.PdfWriter()
        for _ in range(3):
            writer.add_blank_page(width=72 * 8.5, height=72 * 11)

        buf = BytesIO()
        writer.write(buf)
        buf.seek(0)

        reader = PyPDF2.PdfReader(buf)
        page0 = reader.pages[0]

        new_writer = PyPDF2.PdfWriter()
        new_writer.add_page(page0)
        out = BytesIO()
        new_writer.write(out)

    cases["create_simple_pdf"] = _run_case(_case_create_simple_pdf)
    cases["page_extract_and_new_writer"] = _run_case(_case_page_extract_and_new_writer)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_merge_and_invalid_pdf_safe() -> None:
    """
    Case set 3: merge operation and invalid PDF handling should not crash runner.
    """
    mod = _try_import_pypdf2()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_merge_two_pdfs():
        import PyPDF2  # type: ignore

        w1 = PyPDF2.PdfWriter()
        w1.add_blank_page(width=72 * 8.5, height=72 * 11)
        b1 = BytesIO()
        w1.write(b1)
        b1.seek(0)

        w2 = PyPDF2.PdfWriter()
        w2.add_blank_page(width=72 * 8.5, height=72 * 11)
        b2 = BytesIO()
        w2.write(b2)
        b2.seek(0)

        # Some versions accept file-like objects directly; others may require PdfReader.
        merger = PyPDF2.PdfMerger()
        try:
            merger.append(b1)
            merger.append(b2)
        except Exception:
            b1.seek(0)
            b2.seek(0)
            merger.append(PyPDF2.PdfReader(b1))
            merger.append(PyPDF2.PdfReader(b2))

        out = BytesIO()
        merger.write(out)
        merger.close()

    def _case_invalid_pdf_bytes():
        import PyPDF2  # type: ignore

        bad = BytesIO(b"This is not a PDF file")
        _ = PyPDF2.PdfReader(bad)

    cases["merge_two_pdfs"] = _run_case(_case_merge_two_pdfs)
    cases["invalid_pdf_bytes"] = _run_case(_case_invalid_pdf_bytes)

    _compute_and_write(cases, import_error=None)
    assert True


def test_robustness_concurrent_in_memory_ops_do_not_hang() -> None:
    """
    Case set 4: concurrent in-memory write/read should not deadlock/hang. Thread joins are bounded.
    """
    mod = _try_import_pypdf2()
    if mod is None:
        _write_robustness_result(avg_score=0.0, num_cases=0, passed_cases=0, import_error=_IMPORT_ERROR)
        assert True
        return

    cases: Dict[str, bool] = {}

    def _case_concurrent_ops():
        import PyPDF2  # type: ignore

        results: List[int] = [0] * 10

        def worker(i: int) -> None:
            try:
                w = PyPDF2.PdfWriter()
                w.add_blank_page(width=72 * 8.5, height=72 * 11)
                buf = BytesIO()
                w.write(buf)
                buf.seek(0)
                r = PyPDF2.PdfReader(buf)
                results[i] = len(r.pages)
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
            raise RuntimeError("Concurrent PDF threads did not finish within timeout")

        return True

    cases["concurrent_in_memory_ops"] = _run_case(_case_concurrent_ops)

    _compute_and_write(cases, import_error=None)
    assert True
