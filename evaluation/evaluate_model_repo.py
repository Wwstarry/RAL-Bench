import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]


def _ensure_repo_on_sys_path(repo: Path) -> None:
    repo_str = str(repo)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)


class _PytestCollector:
    """Simple pytest plugin to count passed/failed tests."""

    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def pytest_runtest_logreport(self, report):  # type: ignore[override]
        if report.when == "call":
            if report.passed:
                self.passed += 1
            elif report.failed:
                self.failed += 1

    @property
    def total(self) -> int:
        return self.passed + self.failed

    @property
    def pass_ratio(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total


def _run_test_suite(test_rel_path: str, repo_under_test: Path) -> Dict[str, Any]:
    """Run a single test suite via pytest and collect pass ratio."""
    _ensure_repo_on_sys_path(repo_under_test)

    test_path = (ROOT / test_rel_path).resolve()
    if not test_path.exists():
        raise FileNotFoundError(f"Test suite not found: {test_path}")

    plugin = _PytestCollector()

    prev_cwd = os.getcwd()
    try:
        os.chdir(ROOT)
        pytest.main([str(test_path)], plugins=[plugin])
    finally:
        os.chdir(prev_cwd)

    return {
        "path": str(test_path),
        "passed": plugin.passed,
        "failed": plugin.failed,
        "total": plugin.total,
        "pass_ratio": plugin.pass_ratio,
    }


def evaluate(task_file: Path, generated_repo: Path) -> Dict[str, Any]:
    """Evaluate a generated repository using functional and non-functional test suites.

    We first run functional tests, then optional performance and resource test suites.
    Functional and non-functional scores are reported separately.
    The overall score is gated by functional correctness so that non-functional
    quality only matters when the system is basically usable.
    """
    with open(task_file, "r", encoding="utf-8") as f:
        task: Dict[str, Any] = yaml.safe_load(f)

    if not generated_repo.exists():
        raise FileNotFoundError(f"Generated repository not found: {generated_repo}")

    task_id = task.get("task_id", "unknown_task")
    suite_cfg = task.get("test_suite") or {}
    func_rel: Optional[str] = suite_cfg.get("functional")
    perf_rel: Optional[str] = suite_cfg.get("performance")
    res_rel: Optional[str] = suite_cfg.get("resource")

    if not func_rel:
        raise RuntimeError("task.yaml must define test_suite.functional.")

    # Functional tests
    functional = _run_test_suite(func_rel, generated_repo)

    # Performance tests (optional)
    performance: Dict[str, Any] = {
        "path": None,
        "passed": 0,
        "failed": 0,
        "total": 0,
        "pass_ratio": 0.0,
    }
    if perf_rel:
        performance = _run_test_suite(perf_rel, generated_repo)

    # Resource tests (optional)
    resource: Dict[str, Any] = {
        "path": None,
        "passed": 0,
        "failed": 0,
        "total": 0,
        "pass_ratio": 0.0,
    }
    if res_rel:
        resource = _run_test_suite(res_rel, generated_repo)

    # Functional score in [0, 1]
    functional_score = functional["pass_ratio"]

    # Non-functional component scores in [0, 1]
    performance_score = performance["pass_ratio"]
    resource_score = resource["pass_ratio"]

    # Aggregate non-functional score: equal-weight average of available dimensions
    nf_components = []
    if performance["total"] > 0:
        nf_components.append(performance_score)
    if resource["total"] > 0:
        nf_components.append(resource_score)

    if nf_components:
        non_functional_score = sum(nf_components) / len(nf_components)
    else:
        non_functional_score = 0.0

    # Overall score with functional gating:
    # 1) If there are no functional tests, the task is treated as invalid and gets score 0.
    # 2) If functional_score == 0 (all functional tests failed), overall score is 0.
    # 3) Otherwise: Score = F * ((1 - alpha) + alpha * NF)
    #    When F is close to 1, this behaves like a weighted combination of functional
    #    and non-functional scores where functional has higher priority.
    if functional["total"] == 0:
        total_score = 0.0
    elif functional_score <= 0.0:
        total_score = 0.0
    else:
        # Relative weight of non-functional score when functionality is satisfied.
        # Alpha = 0.4 roughly corresponds to (0.6 * F + 0.4 * NF) when F is close to 1.
        alpha = 0.4
        total_score = functional_score * ((1 - alpha) + alpha * non_functional_score)

    result: Dict[str, Any] = {
        "task_id": task_id,
        "functional": {
            "path": functional["path"],
            "passed": functional["passed"],
            "failed": functional["failed"],
            "total": functional["total"],
            "pass_ratio": round(functional_score, 3),
        },
        "performance": {
            "path": performance["path"],
            "passed": performance["passed"],
            "failed": performance["failed"],
            "total": performance["total"],
            "pass_ratio": round(performance_score, 3),
        },
        "resource": {
            "path": resource["path"],
            "passed": resource["passed"],
            "failed": resource["failed"],
            "total": resource["total"],
            "pass_ratio": round(resource_score, 3),
        },
        "non_functional": {
            "score": round(non_functional_score, 3),
        },
        "total_score": round(total_score, 3),
    }

    out_path = generated_repo / f"result_{task_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    default_task = ROOT / "tasks" / "Stegano" / "stegano.yaml"
    default_gen = ROOT / "generation" / "Stegano"
    default_gen.mkdir(parents=True, exist_ok=True)
    evaluate(default_task, default_gen)
