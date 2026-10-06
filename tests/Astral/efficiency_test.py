from __future__ import annotations

import datetime as dt
import os
import sys
import time
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[2]
REPO_ROOT_ENV = "RACB_REPO_ROOT"


def _select_repo_root() -> Path:
    override = os.environ.get(REPO_ROOT_ENV)
    if override:
        return Path(override).resolve()

    target = os.environ.get("ASTRAL_TARGET", "generated").lower()
    if target == "reference":
        for name in ("Astral", "astral"):
            cand = ROOT / "repositories" / name
            if cand.exists():
                return cand.resolve()
        return (ROOT / "repositories" / "Astral").resolve()
    return (ROOT / "generation" / "Astral").resolve()


REPO_ROOT = _select_repo_root()


def _ensure_import_path(repo_root: Path) -> None:
    src = repo_root / "src"
    sys_path_entry = str(src if src.exists() else repo_root)
    if sys_path_entry not in sys.path:
        sys.path.insert(0, sys_path_entry)


_ensure_import_path(REPO_ROOT)

from astral import LocationInfo  # type: ignore
from astral.sun import sun  # type: ignore


def _london_location() -> LocationInfo:
    return LocationInfo("London", "England", "Europe/London", 51.5074, -0.1278)


def run_astral_performance_benchmark(iterations: int = 10, days: int = 30) -> Dict[str, float]:
    """Run repeated sun() calculations and report simple timing metrics."""
    loc = _london_location()
    base_date = dt.date(2020, 1, 1)

    total_calls = 0

    t0 = time.perf_counter()
    for _ in range(iterations):
        for offset in range(days):
            d = base_date + dt.timedelta(days=offset)
            _ = sun(loc.observer, date=d, tzinfo=loc.timezone)
            total_calls += 1
    total_time = time.perf_counter() - t0

    return {
        "iterations": float(iterations),
        "days_per_iteration": float(days),
        "total_calls": float(total_calls),
        "total_time_seconds": float(total_time),
        "calls_per_second": float(total_calls / total_time) if total_time > 0 else 0.0,
    }


def test_astral_performance_smoke() -> None:
    """Smoke test to ensure the performance benchmark runs successfully."""
    metrics = run_astral_performance_benchmark(iterations=5, days=10)
    assert metrics["iterations"] == 5.0
    assert metrics["days_per_iteration"] == 10.0
    assert metrics["total_calls"] == 50.0
    assert metrics["total_time_seconds"] >= 0.0
    assert metrics["calls_per_second"] >= 0.0
