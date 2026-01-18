import os
import sys
import time
from pathlib import Path
from typing import Dict


TARGET_ENV = "REQUESTS_TARGET"
ROOT_DIR = Path(__file__).resolve().parents[2]


def _looks_like_repo_root(repo_root: Path) -> bool:
    return (repo_root / "requests" / "__init__.py").exists()


def _select_repo_root() -> Path:
    override = os.environ.get("RACB_REPO_ROOT")
    if override:
        p = Path(override).resolve()
        if _looks_like_repo_root(p):
            return p

    target = os.environ.get(TARGET_ENV, "generated").lower()
    if target == "reference":
        return (ROOT_DIR / "repositories" / "requests").resolve()

    return (ROOT_DIR / "generation" / "Requests").resolve()


REPO_ROOT = _select_repo_root()
repo_str = str(REPO_ROOT)
if repo_str not in sys.path:
    sys.path.insert(0, repo_str)

import requests  # noqa: E402


def run_requests_prepare_benchmark(iterations: int = 5000) -> Dict[str, float]:
    s = requests.Session()
    url = "http://example.invalid/path"  # only used to prepare, not to send
    t0 = time.perf_counter()
    for _ in range(iterations):
        req = requests.Request("GET", url, headers={"X": "1"})
        _ = s.prepare_request(req)
    elapsed = time.perf_counter() - t0
    s.close()
    return {
        "iterations": float(iterations),
        "total_time_seconds": float(elapsed),
        "calls_per_second": float(iterations / elapsed) if elapsed > 0 else 0.0,
    }


def test_requests_performance_smoke() -> None:
    m = run_requests_prepare_benchmark(iterations=1000)
    assert m["iterations"] == 1000.0
    assert m["total_time_seconds"] >= 0.0
    assert m["calls_per_second"] >= 0.0
