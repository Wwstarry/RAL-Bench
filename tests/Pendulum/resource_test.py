from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("PENDULUM_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "pendulum"
else:
    REPO_ROOT = ROOT / "generation" / "Pendulum"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

src_dir = REPO_ROOT / "src"
if src_dir.exists():
    import_root = src_dir
else:
    import_root = REPO_ROOT

if str(import_root) not in sys.path:
    sys.path.insert(0, str(import_root))

import pendulum  # type: ignore  # noqa: E402


def test_generate_recurring_schedule_and_group_by_day() -> None:
    """
    Integration-style test: build a recurring schedule, convert to another
    timezone, and group events by local calendar day.
    """
    # Start from a fixed UTC anchor.
    start = pendulum.datetime(2022, 1, 1, 8, 0, 0, tz="UTC")

    # Create a small weekly schedule with three "meetings" per day.
    meetings_utc = []
    for day in range(7):
        for hour in (9, 13, 17):
            meetings_utc.append(start.add(days=day, hours=hour))

    tz_tokyo = pendulum.timezone("Asia/Tokyo")
    meetings_local = [m.in_timezone(tz_tokyo) for m in meetings_utc]

    # Group by local date string.
    grouped: dict[str, list[pendulum.DateTime]] = {}
    for m in meetings_local:
        key = m.to_date_string()
        grouped.setdefault(key, []).append(m)

    # We expect at least several distinct local days.
    assert len(grouped) >= 5

    # Within each day, meetings should be in increasing time order.
    for day, events in grouped.items():
        hours = [e.hour for e in events]
        assert hours == sorted(hours)

    # Simple consistency check: total count preserved.
    assert len(meetings_local) == len(meetings_utc)
