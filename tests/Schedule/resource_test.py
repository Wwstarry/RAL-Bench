import os
import sys
from pathlib import Path

import psutil  # type: ignore

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


def test_scheduler_resource_usage_smoke() -> None:
    """
    Rough resource-usage sanity check for registering and running many jobs.

    The goal is to exercise the scheduler with a moderate number of jobs and
    sample memory and CPU usage, not to enforce a particular limit.
    """
    proc = psutil.Process(os.getpid())

    schedule.clear()
    calls = 0

    def job() -> None:
        nonlocal calls
        calls += 1

    # Register a moderate number of jobs
    for _ in range(300):
        schedule.every().seconds.do(job)

    mem_samples = []
    cpu_samples = []

    for _ in range(5):
        schedule.run_all()
        mem_samples.append(proc.memory_info().rss)
        cpu_samples.append(proc.cpu_percent(interval=0.05))

    avg_mem_mb = sum(mem_samples) / len(mem_samples) / (1024 * 1024)
    avg_cpu = sum(cpu_samples) / len(cpu_samples)

    print(f"Average memory: {avg_mem_mb:.2f} MB, CPU: {avg_cpu:.2f}%")
    assert avg_mem_mb >= 0.0
    assert avg_cpu >= 0.0
    assert calls > 0
