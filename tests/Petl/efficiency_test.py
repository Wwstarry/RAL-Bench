from __future__ import annotations

import csv
import os
import sys
import time
import types
from pathlib import Path
from typing import Any, Dict, List

import pytest

ROOT = Path(__file__).resolve().parents[2]

TARGET_ENV = os.getenv("PETL_TARGET", "reference")
if TARGET_ENV == "reference":
    REPO_ROOT = ROOT / "repositories" / "Petl"
elif TARGET_ENV == "generation":
    REPO_ROOT = ROOT / "generation" / "Petl"
else:
    raise RuntimeError(f"Unsupported PETL_TARGET value: {TARGET_ENV}")

if not REPO_ROOT.exists():
    raise RuntimeError(f"Repository root does not exist: {REPO_ROOT}")

if (REPO_ROOT / "petl").exists():
    PACKAGE_ROOT = REPO_ROOT
else:
    raise RuntimeError(f"Could not find 'petl' package directory under {REPO_ROOT}")

sys.path.insert(0, str(PACKAGE_ROOT))

version_module_path = PACKAGE_ROOT / "petl" / "version.py"
if not version_module_path.exists():
    stub = types.ModuleType("petl.version")
    stub.version = "0.0.0"
    sys.modules["petl.version"] = stub

import petl  # type: ignore[import]


def _generate_large_csv(path: Path, num_rows: int = 20000) -> None:
    """Generate a moderately large CSV file with predictable content."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["id", "group", "value"])
        for i in range(num_rows):
            group = f"g{i % 10}"
            value = i % 1000
            writer.writerow([i, group, value])


def test_bulk_csv_pipeline_performance(tmp_path: Path) -> None:
    """Measure performance of a CSV-based ETL pipeline on a larger dataset."""
    source_csv = tmp_path / "input.csv"
    output_csv = tmp_path / "output.csv"

    _generate_large_csv(source_csv, num_rows=20000)

    start = time.perf_counter()

    table = petl.fromcsv(str(source_csv))
    table = petl.convert(table, "value", int)
    table = petl.selectgt(table, "value", 500)
    table = petl.sort(table, "value")
    petl.tocsv(table, str(output_csv))

    elapsed = time.perf_counter() - start

    assert output_csv.exists()
    assert elapsed < 15.0


def test_large_fromdicts_addfield_pipeline_performance() -> None:
    """Measure performance of fromdicts/addfield/select/materialization pipeline."""
    records: List[Dict[str, Any]] = []
    for i in range(25000):
        records.append(
            {
                "id": i,
                "group": f"g{i % 5}",
                "value": i % 1000,
            }
        )

    start = time.perf_counter()

    table = petl.fromdicts(records, header=["id", "group", "value"])
    table = petl.addfield(table, "score", lambda rec: int(rec["value"]) * 3)
    table = petl.selectge(table, "score", 1500)

    # Force evaluation of the lazy pipeline.
    rows = list(table)
    assert len(rows) > 1

    elapsed = time.perf_counter() - start
    assert elapsed < 15.0
