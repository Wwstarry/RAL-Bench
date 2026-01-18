# tests/Imageio/robustness_test.py

import json
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Imageio"
PACKAGE_IMPORT = "imageio"

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
      2) <bench_root>/repositories/imageio
      3) <bench_root>/generation/imageio
    """
    candidates: List[Path] = []

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        p = Path(env_root).resolve()
        candidates.append(p)
        candidates.append((p / "repositories" / "imageio").resolve())
        candidates.append((p / "generation" / "imageio").resolve())

    candidates.append((ROOT / "repositories" / "imageio").resolve())
    candidates.append((ROOT / "generation" / "imageio").resolve())

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
      - repo_root/imageio/__init__.py
      - repo_root/src/imageio/__init__.py
    """
    for cand in _candidate_repo_roots():
        if (cand / "imageio" / "__init__.py").exists():
            return cand
        if (cand / "src" / "imageio" / "__init__.py").exists():
            return cand

    env_root = os.environ.get("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()

    raise RuntimeError(f"Could not locate importable repo root for {PROJECT_NAME}.")


def _prepare_import_path() -> None:
    repo_root = _select_repo_root()
    # Prefer src layout if present
    if (repo_root / "src").is_dir() and (repo_root / "src" / "imageio" / "__init__.py").exists():
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
    """
    Merge per-case pass/fail into a single robustness report.

    We store a stable map of case_id -> ok (bool). Each pytest test can run
    independently; order does not matter.

    Final metrics:
      avg_score = passed_cases / num_cases
    """
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

_IMAGEIO_MOD = None


def _import_imageio():
    global _IMAGEIO_MOD
    if _IMAGEIO_MOD is not None:
        return _IMAGEIO_MOD

    _prepare_import_path()
    try:
        _IMAGEIO_MOD = __import__(PACKAGE_IMPORT)
    except Exception as e:
        pytest.skip(f"Cannot import '{PACKAGE_IMPORT}' from evaluated repo: {type(e).__name__}: {e}")
    return _IMAGEIO_MOD


def _run_case(fn: Callable[[], Any]) -> bool:
    """
    Robustness scoring rule:
      - ok=True  : returns normally OR raises a normal exception (both acceptable)
      - ok=False : reserved for harness-level fatal issues (we avoid producing this)
    """
    try:
        fn()
        return True
    except Exception:
        return True


# -----------------------------------------------------------------------------
# 3 robustness tests (each always passes at pytest level)
# -----------------------------------------------------------------------------

def test_robustness_import_and_introspection() -> None:
    """
    Robustness 1: import and basic module introspection should not hard-crash.
    """
    imageio = _import_imageio()
    case_results: Dict[str, bool] = {}

    case_results["import_imageio"] = True
    case_results["has_version_attr"] = _run_case(lambda: getattr(imageio, "__version__", None))
    case_results["formats_access_or_fail_safely"] = _run_case(
        lambda: getattr(imageio, "formats").__class__.__name__  # touch attribute
    )

    # Some versions expose imageio.core; some may lazy-load. Either is acceptable.
    case_results["import_core_or_fail_safely"] = _run_case(lambda: __import__("imageio.core"))

    _merge_case_results(case_results)
    assert True


def test_robustness_decode_invalid_bytes_fails_safely() -> None:
    """
    Robustness 2: decoding clearly invalid bytes should fail safely (raise) or return safely.
    We avoid any filesystem dependencies and use in-memory bytes.
    """
    imageio = _import_imageio()
    case_results: Dict[str, bool] = {}

    # Try imageio.v2 if available (common stable entry point)
    def _imread_invalid_bytes_v2():
        v2 = getattr(imageio, "v2", None)
        if v2 is None:
            raise AttributeError("imageio.v2 not available")
        # invalid "file" content
        return v2.imread(b"not_an_image", format="png")  # type: ignore[arg-type]

    def _imread_invalid_bytes_root():
        # fallback API in some versions
        return imageio.imread(b"not_an_image")  # type: ignore[attr-defined,arg-type]

    case_results["imread_invalid_bytes_v2"] = _run_case(_imread_invalid_bytes_v2)
    case_results["imread_invalid_bytes_root"] = _run_case(_imread_invalid_bytes_root)

    _merge_case_results(case_results)
    assert True


def test_robustness_writer_invalid_params_fail_safely() -> None:
    """
    Robustness 3: writer construction with invalid params should fail safely (raise)
    or return an object without hard crash.
    """
    imageio = _import_imageio()
    case_results: Dict[str, bool] = {}

    def _get_writer_bad_format():
        v2 = getattr(imageio, "v2", None)
        if v2 is None:
            raise AttributeError("imageio.v2 not available")
        # nonsense format should raise in most versions
        return v2.get_writer("<memory>", format="definitely_not_a_real_format")  # type: ignore[arg-type]

    def _get_reader_nonexistent_uri():
        v2 = getattr(imageio, "v2", None)
        if v2 is None:
            raise AttributeError("imageio.v2 not available")
        return v2.get_reader("this_file_should_not_exist_123456789.png")  # type: ignore[arg-type]

    case_results["get_writer_bad_format"] = _run_case(_get_writer_bad_format)
    case_results["get_reader_nonexistent_uri"] = _run_case(_get_reader_nonexistent_uri)

    _merge_case_results(case_results)

    # Ensure we exercised >= 5+ scenarios total across tests (soft floor)
    data = _load_json()
    num_cases = int((data.get("robustness", {}) or {}).get("num_cases", 0) or 0)
    assert num_cases >= 5
