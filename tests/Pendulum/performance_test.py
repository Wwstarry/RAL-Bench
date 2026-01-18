from __future__ import annotations

import os
import sys
import time
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


def test_many_datetime_operations() -> None:
    """
    Exercise many datetime operations to give the benchmark
    something non-trivial to time.
    """
    base = pendulum.datetime(2020, 1, 1, 0, 0, 0, tz="UTC")
    results: list[str] = []

    start_time = time.perf_counter()

    for i in range(2000):
        dt = base.add(minutes=i)
        tokyo = dt.in_timezone("Asia/Tokyo")
        ny = dt.in_timezone("America/New_York")

        # Format to strings to force some extra work.
        results.append(tokyo.to_iso8601_string())
        results.append(ny.to_iso8601_string())

    elapsed = time.perf_counter() - start_time

    # Lightweight sanity checks (no strict timing assertion).
    assert len(results) == 4000
    assert elapsed >= 0.0
