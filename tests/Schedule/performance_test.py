import os
import sys
import time
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("SCHEDULE_TARGET", "generated").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "schedule"
else:
    REPO_ROOT = ROOT / "generation" / "Schedule"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Repository root does not exist: {REPO_ROOT}")

sys.path.insert(0, str(REPO_ROOT))

import schedule  # type: ignore  # noqa: E402


def _measure_scheduler_run_all(num_jobs: int = 500, num_runs: int = 5) -> float:
    """Register a number of jobs and call run_all several times."""
    schedule.clear()
    counter = 0

    def job() -> None:
        nonlocal counter
        counter += 1

    for _ in range(num_jobs):
        schedule.every().seconds.do(job)

    timings = []
    for _ in range(num_runs):
        start = time.perf_counter()
        schedule.run_all()
        timings.append(time.perf_counter() - start)

    return statistics.mean(timings)


def test_schedule_performance_smoke() -> None:
    """Simple performance sanity check for the scheduler."""
    avg = _measure_scheduler_run_all()
    print(f"Average run_all duration over many jobs: {avg:.6f}s")
    assert avg > 0.0
