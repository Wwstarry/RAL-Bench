from __future__ import annotations

import os
import sys
import time
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


def _build_large_dataset(num_rows: int = 10000) -> "tablib.Dataset":
    """Create a dataset with a predictable structure and many rows."""
    data = tablib.Dataset()
    data.headers = ("index", "group", "value")

    for i in range(num_rows):
        group = f"g{i % 10}"
        value = float(i % 100)
        data.append((i, group, value))

    return data


def test_bulk_export_csv_and_json_performance() -> None:
    """
    Measure performance of bulk CSV/JSON export on a moderately large dataset.

    The threshold is intentionally generous so that the test remains stable
    across a variety of machines while still producing a useful baseline.
    """
    data = _build_large_dataset(num_rows=10000)

    start = time.perf_counter()
    csv_text = data.export("csv")
    json_text = data.export("json")
    elapsed = time.perf_counter() - start

    # Sanity checks: both exports should produce non-empty strings.
    assert isinstance(csv_text, str) and len(csv_text) > 0
    assert isinstance(json_text, str) and len(json_text) > 0

    # Allow plenty of headroom; the real measurements are recorded by the harness.
    assert elapsed < 10.0


def test_repeated_dataset_exports_are_reasonably_fast() -> None:
    """
    Run multiple export operations to capture a coarse throughput baseline.

    This exercises internal caching and formatting paths without being
    a micro-benchmark.
    """
    data = _build_large_dataset(num_rows=5000)

    start = time.perf_counter()
    for _ in range(10):
        _ = data.export("csv")
        _ = data.export("json")
    elapsed = time.perf_counter() - start

    # The loop should complete within a generous time bound.
    assert elapsed < 15.0
