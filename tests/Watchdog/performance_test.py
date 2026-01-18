from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Dict

import pytest

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("WATCHDOG_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "watchdog" / "src"
else:
    REPO_ROOT = ROOT / "generation" / "Watchdog"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from watchdog.observers import Observer  # type: ignore  # noqa: E402
from watchdog.events import FileSystemEventHandler  # type: ignore  # noqa: E402


class _Counter(FileSystemEventHandler):
    """Simple handler that counts created events."""

    def __init__(self) -> None:
        super().__init__()
        self.count = 0

    def on_created(self, event) -> None:  # type: ignore[override]
        self.count += 1


def run_watchdog_benchmark(tmp: Path, n: int = 80) -> Dict[str, float]:
    """Create n files and measure how many created events are observed."""
    handler = _Counter()
    obs = Observer()
    obs.schedule(handler, str(tmp), recursive=False)

    start = time.perf_counter()
    obs.start()

    for i in range(n):
        (tmp / f"f{i}.txt").write_text("x")
    time.sleep(0.3)

    obs.stop()
    obs.join(timeout=1)
    end = time.perf_counter()

    return {
        "events_expected": float(n),
        "events_recorded": float(handler.count),
        "total_time_s": float(end - start),
    }


def test_watchdog_performance_smoke(tmp_path: Path) -> None:
    """Smoke test to ensure the performance benchmark runs successfully."""
    metrics = run_watchdog_benchmark(tmp_path, n=40)
    assert metrics["events_recorded"] >= 1.0
    assert metrics["total_time_s"] >= 0.0
