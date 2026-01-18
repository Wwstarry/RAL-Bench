from __future__ import annotations

import os
import sys
import tracemalloc
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

TARGET_ENV = os.getenv("TABLIB_TARGET", "reference")
if TARGET_ENV == "reference":
    REPO_ROOT = ROOT / "repositories" / "Tablib"
elif TARGET_ENV == "generation":
    REPO_ROOT = ROOT / "generation" / "Tablib"
else:
    raise RuntimeError(f"Unsupported TABLIB_TARGET value: {TARGET_ENV}")

if not REPO_ROOT.exists():
    raise RuntimeError(f"Repository root does not exist: {REPO_ROOT}")

# Support both flat and src/ package layouts.
if (REPO_ROOT / "tablib").exists():
    PACKAGE_ROOT = REPO_ROOT
elif (REPO_ROOT / "src" / "tablib").exists():
    PACKAGE_ROOT = REPO_ROOT / "src"
else:
    raise RuntimeError(f"Could not find 'tablib' package in {REPO_ROOT}")

sys.path.insert(0, str(PACKAGE_ROOT))

import tablib  # type: ignore[import]


def _bulk_dataset_workload(repeat: int = 5, rows_per_dataset: int = 5000) -> None:
    """
    Build several datasets and export them to exercise memory usage patterns.
    """
    for r in range(repeat):
        data = tablib.Dataset()
        data.headers = ("idx", "bucket", "value")

        for i in range(rows_per_dataset):
            bucket = f"b{i % 8}"
            value = (r + 1) * i
            data.append((i, bucket, value))

        # Export to a couple of formats to trigger formatter code paths.
        _ = data.export("csv")
        _ = data.export("json")


def _databook_workload() -> None:
    """
    Construct multiple small Databooks to exercise aggregation behavior.
    """
    for _ in range(10):
        sheets = []
        for j in range(3):
            ds = tablib.Dataset()
            ds.headers = ("id", "value")
            for i in range(1000):
                ds.append((i, f"s{j}-{i}"))
            ds.title = f"Sheet-{j}"
            sheets.append(ds)
        book = tablib.Databook(sheets)
        _ = book.export("json")


def test_memory_usage_under_bulk_dataset_operations() -> None:
    """
    Ensure that repeated dataset creation and export stay within a coarse memory bound.
    """
    tracemalloc.start()

    _bulk_dataset_workload()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # Coarse upper bound to catch obvious leaks while remaining tolerant
    # of allocator differences.
    max_allowed_bytes = 120 * 1024 * 1024
    assert peak < max_allowed_bytes


def test_memory_usage_under_databook_operations() -> None:
    """
    Build and export multiple Databooks to check for unbounded growth.
    """
    tracemalloc.start()

    _databook_workload()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    max_allowed_bytes = 80 * 1024 * 1024
    assert peak < max_allowed_bytes
