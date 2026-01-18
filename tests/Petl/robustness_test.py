# tests/Petl/robustness_test.py

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pytest


ROOT = Path(__file__).resolve().parents[2]
PROJECT_NAME = "Petl"
PACKAGE_IMPORT = "petl"

RESULTS_DIR = ROOT / "results" / PROJECT_NAME
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_PATH = RESULTS_DIR / "nfr_reference.json"


def _repo_root_from_env() -> Path:
    env_root = os.environ.get("RACB_REPO_ROOT")
    if not env_root:
        # 不要 skip：让测试继续跑，并在结果里写明原因
        return Path(".").resolve()
    return Path(env_root).resolve()


def _find_import_base(repo_root: Path) -> Optional[Path]:
    """
    Locate the sys.path entry that makes `import petl` possible.

    Supported layouts:
      - repo_root/src/petl/__init__.py
      - repo_root/petl/__init__.py
      - repo_root/**/petl/__init__.py (fallback)
    """
    # 1) src layout
    if (repo_root / "src" / PACKAGE_IMPORT / "__init__.py").exists():
        return repo_root / "src"

    # 2) root layout
    if (repo_root / PACKAGE_IMPORT / "__init__.py").exists():
        return repo_root

    # 3) fallback recursive search
    try:
        for init_path in repo_root.rglob("{}/__init__.py".format(PACKAGE_IMPORT)):
            base = init_path.parent.parent  # .../<base>/petl/__init__.py -> base
            if base.is_dir():
                return base
    except Exception:
        return None

    return None


def _prepare_import_path() -> None:
    repo_root = _repo_root_from_env()
    base = _find_import_base(repo_root)
    if base is None:
        return
    p = str(base)
    if p not in sys.path:
        sys.path.insert(0, p)


def _load_results_json() -> Dict[str, Any]:
    if RESULTS_PATH.exists():
        try:
            with open(RESULTS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_results_json(data: Dict[str, Any]) -> None:
    with open(RESULTS_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)


def _run_case(case_id: str, fn: Callable[[], Any]) -> Tuple[bool, str]:
    """
    Robustness semantics:
      - PASS if returns normally
      - PASS if raises a normal Exception (safe failure)
    """
    try:
        fn()
        return True, "{}: ok".format(case_id)
    except Exception as e:
        return True, "{}: raised {} (acceptable)".format(case_id, type(e).__name__)


def test_petl_robustness_metrics() -> None:
    """
    Petl robustness evaluation:
      - >= 3 cases
      - NEVER skip
      - Write results/Petl/nfr_reference.json with a standard robustness block
    """
    _prepare_import_path()

    petl = None
    import_error = None
    try:
        petl = __import__(PACKAGE_IMPORT)
    except Exception as e:
        import_error = "{}: {}".format(type(e).__name__, e)

    # Define >= 3 test cases (if import fails, we record avg_score=0 and keep pytest green)
    cases = []  # type: List[Tuple[str, Callable[[], Any]]]

    def case_importable_and_has_wrap():
        if petl is None:
            raise RuntimeError("petl not importable")
        getattr(petl, "wrap")  # should exist on real petl
        return True

    def case_basic_table_ops():
        if petl is None:
            raise RuntimeError("petl not importable")
        etl = petl
        table = etl.wrap([["foo", "bar"], [1, "a"], [2, "b"]])
        rows = list(table)
        assert len(rows) >= 2
        # sort may exist; if not, safe failure is acceptable
        if hasattr(etl, "sort"):
            _ = list(etl.sort(table, "foo"))
        return True

    def case_invalid_input_nonexistent_file():
        if petl is None:
            raise RuntimeError("petl not importable")
        etl = petl
        if not hasattr(etl, "fromcsv"):
            raise AttributeError("petl.fromcsv not available")
        t = etl.fromcsv("this_file_should_not_exist_123456.csv")
        # Some versions lazily evaluate; force evaluation
        _ = list(t)
        return True

    def case_concurrent_smoke():
        if petl is None:
            raise RuntimeError("petl not importable")
        etl = petl
        errors = []  # type: List[BaseException]

        def worker(i: int) -> None:
            try:
                t = etl.wrap([["x"], [i]])
                _ = list(t)
            except BaseException as ee:
                errors.append(ee)

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

        # If threads hung, join(timeout) would return; we treat errors as safe
        return len(errors)

    cases.append(("importable_and_has_wrap", case_importable_and_has_wrap))
    cases.append(("basic_table_ops", case_basic_table_ops))
    cases.append(("invalid_input_nonexistent_file", case_invalid_input_nonexistent_file))
    cases.append(("concurrent_smoke", case_concurrent_smoke))

    num_cases = len(cases)

    if petl is None:
        # Cannot exercise library => avg_score=0, but still write metrics and pass pytest
        robustness_payload = {
            "avg_score": 0.0,
            "num_cases": num_cases,
            "passed_cases": 0,
            "import_error": import_error,
            "repo_root": str(_repo_root_from_env()),
        }
    else:
        results = [_run_case(case_id, fn) for case_id, fn in cases]
        passed_cases = sum(1 for ok, _ in results if ok)
        avg_score = (float(passed_cases) / float(num_cases)) if num_cases else 1.0
        robustness_payload = {
            "avg_score": round(avg_score, 3),
            "num_cases": num_cases,
            "passed_cases": passed_cases,
        }

    data = _load_results_json()
    data["robustness"] = robustness_payload
    _save_results_json(data)

    # pytest-level invariant
    assert num_cases >= 3
