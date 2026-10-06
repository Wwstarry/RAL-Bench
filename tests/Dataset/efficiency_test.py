from __future__ import annotations

import os
import sys
import time
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
    """Create a lightweight in-memory SQLite database."""
    return dataset.connect("sqlite:///:memory:")


def test_bulk_insert_and_filtered_query_performance() -> None:
    """
    Measure bulk insert and filtered querying performance.

    The thresholds are intentionally generous so that the test
    remains stable across a variety of machines while still
    providing a useful baseline for comparisons.
    """
    db = create_in_memory_db()
    table = db["measurements"]

    num_rows = 10000
    rows = [
        {
            "id": i,
            "sensor": f"s{i % 10}",
            "value": float(i % 100),
            "bucket": "high" if i % 2 == 0 else "low",
        }
        for i in range(num_rows)
    ]

    start = time.perf_counter()
    table.insert_many(rows, chunk_size=1000)

    assert table.count() == num_rows

    # Run a filtered query and materialize the results.
    filtered = list(table.find(bucket="high", value={">=": 50}))
    # Sanity check on result size.
    assert len(filtered) > 0

    elapsed = time.perf_counter() - start

    # Allow plenty of headroom; the actual value will be
    # recorded by the benchmarking harness.
    assert elapsed < 10.0


def test_indexed_query_scaling_with_row_count() -> None:
    """
    Compare indexed vs non-indexed queries at a coarse granularity.

    The goal is not micro-benchmark accuracy but to ensure that
    index creation works and that queries remain reasonably fast.
    """
    db = create_in_memory_db()
    table = db["events"]

    small_rows = [
        {"event_id": i, "kind": "small", "tag": f"t{i % 5}"}
        for i in range(1000)
    ]
    large_rows = [
        {"event_id": 1000 + i, "kind": "large", "tag": f"t{i % 5}"}
        for i in range(9000)
    ]
    table.insert_many(small_rows)
    table.insert_many(large_rows)

    # Unindexed query.
    t0 = time.perf_counter()
    unindexed_result = list(table.find(kind="large", tag="t1"))
    t1 = time.perf_counter()
    assert len(unindexed_result) > 0

    # Create an index and run the same query again.
    table.create_index(["kind", "tag"])
    t2 = time.perf_counter()
    indexed_result = list(table.find(kind="large", tag="t1"))
    t3 = time.perf_counter()

    assert len(indexed_result) == len(unindexed_result)

    unindexed_time = t1 - t0
    indexed_time = t3 - t2

    # The indexed query should not be significantly slower.
    # We use a generous factor to keep the test robust.
    if unindexed_time > 0:
        assert indexed_time < unindexed_time * 3.0
