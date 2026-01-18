from __future__ import annotations

import os
import sys
import tracemalloc
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

TARGET_ENV = os.getenv("DATASET_TARGET", "reference")
if TARGET_ENV == "reference":
    REPO_ROOT = ROOT / "repositories" / "Dataset"
elif TARGET_ENV == "generation":
    REPO_ROOT = ROOT / "generation" / "Dataset"
else:
    raise RuntimeError(f"Unsupported DATASET_TARGET value: {TARGET_ENV}")

if not REPO_ROOT.exists():
    raise RuntimeError(f"Repository root does not exist: {REPO_ROOT}")

sys.path.insert(0, str(REPO_ROOT))

import dataset  # type: ignore[import]


def create_in_memory_db() -> "dataset.Database":
    """Create a fresh in-memory SQLite database."""
    return dataset.connect("sqlite:///:memory:")


def _run_bulk_workload() -> None:
    """Helper that performs a moderately sized workload on a table."""
    db = create_in_memory_db()
    table = db["logs"]

    rows = [
        {
            "seq": i,
            "level": "INFO" if i % 5 else "WARN",
            "component": f"c{i % 7}",
            "message": f"message-{i}",
        }
        for i in range(15000)
    ]
    table.insert_many(rows, chunk_size=1000)

    # Run a couple of filtered queries and iterate over results.
    warn_rows = list(table.find(level="WARN"))
    assert len(warn_rows) > 0

    # Delete a subset of rows to exercise write paths.
    table.delete(level="INFO")

    remaining = list(table.all())
    assert all(row["level"] == "WARN" for row in remaining)


def test_memory_usage_under_bulk_workload() -> None:
    """
    Ensure bulk operations keep memory consumption within a reasonable bound.

    This is primarily a regression guard: it should detect gross leaks
    while staying tolerant of normal allocator behavior.
    """
    tracemalloc.start()

    _run_bulk_workload()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Require that peak memory usage stays well below 100 MB.
    # The exact value is not important; it is a coarse sanity check.
    max_allowed_bytes = 100 * 1024 * 1024
    assert peak < max_allowed_bytes


def test_repeated_connections_do_not_leak_tables() -> None:
    """
    Open and use multiple connections to check that resource usage remains bounded.
    """
    tracemalloc.start()

    for i in range(5):
        db = create_in_memory_db()
        table = db["session_data"]
        table.insert({"session": f"s{i}", "value": i})
        assert table.count() == 1

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Again use a generous threshold to make the test stable.
    max_allowed_bytes = 80 * 1024 * 1024
    assert peak < max_allowed_bytes
