from __future__ import annotations

import datetime as dt
import os
import sys
import time
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("DATEUTIL_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "dateutil" / "src"
else:
    REPO_ROOT = ROOT / "generation" / "Dateutil"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dateutil import parser, tz  # type: ignore  # noqa: E402
from dateutil.rrule import rrule, DAILY  # type: ignore  # noqa: E402


def _sample_datetime_strings() -> List[str]:
    """Return a list of datetime strings in different formats."""
    return [
        "2020-01-01T12:00:00Z",
        "2020-03-15 08:30:45+02:00",
        "April 5, 2021 7:15 pm UTC",
        "2022-11-30",
        "2023-07-01 00:00",
    ]


def run_dateutil_performance_benchmark(
    iterations: int = 100, rrule_span_days: int = 365
) -> dict[str, float]:
    """Run repeated parsing and recurrence generation and measure total time."""
    strings = _sample_datetime_strings()
    # Use a fixed-offset timezone (UTC-5) instead of named zone.
    ny = tz.tzoffset("NY", -5 * 3600)

    parse_calls = 0
    rrule_events = 0

    base_start = dt.datetime(2020, 1, 1, tzinfo=tz.UTC)

    t0 = time.perf_counter()
    for i in range(iterations):
        # Parsing benchmark
        for s in strings:
            dt_obj = parser.parse(s)
            # Convert to another timezone to exercise tz handling.
            _ = dt_obj.astimezone(ny)
            parse_calls += 1

        # Recurrence generation benchmark
        start = base_start + dt.timedelta(days=i)
        rule = rrule(DAILY, dtstart=start, count=rrule_span_days)
        for _ in rule:
            rrule_events += 1
    t1 = time.perf_counter()

    total_time = t1 - t0

    return {
        "iterations": float(iterations),
        "parse_calls": float(parse_calls),
        "rrule_events": float(rrule_events),
        "total_time_seconds": float(total_time),
        "operations_per_second": float((parse_calls + rrule_events) / total_time)
        if total_time > 0
        else 0.0,
    }


def test_dateutil_performance_smoke() -> None:
    """Smoke test to ensure the performance benchmark runs successfully."""
    metrics = run_dateutil_performance_benchmark(iterations=10, rrule_span_days=30)
    assert metrics["iterations"] == 10.0
    assert metrics["parse_calls"] > 0.0
    assert metrics["rrule_events"] > 0.0
    assert metrics["total_time_seconds"] >= 0.0
    assert metrics["operations_per_second"] >= 0.0
