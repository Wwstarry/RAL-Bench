from __future__ import annotations

import os
import sys
import tracemalloc
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


def _bulk_fromdicts_and_transforms(repeat: int = 5, rows_per_batch: int = 8000) -> None:
    """Apply repeated fromdicts/addfield/select pipelines to exercise memory usage."""
    for r in range(repeat):
        records: List[Dict[str, Any]] = []
        for i in range(rows_per_batch):
            records.append(
                {
                    "id": i,
                    "batch": r,
                    "value": (i * (r + 1)) % 1000,
                }
            )

        table = petl.fromdicts(records, header=["id", "batch", "value"])
        table = petl.addfield(table, "double", lambda rec: int(rec["value"]) * 2)
        table = petl.selectge(table, "double", 500)

        # Materialize a subset to ensure the pipeline is actually evaluated.
        _ = list(petl.head(table, 100))


def _bulk_csv_roundtrips(tmp_path: Path, repeat: int = 4, rows_per_file: int = 5000) -> None:
    """Perform several CSV roundtrips via fromcsv/tocsv on temporary files."""
    for r in range(repeat):
        source = tmp_path / f"input_{r}.csv"
        target = tmp_path / f"output_{r}.csv"

        with source.open("w", newline="", encoding="utf-8") as f:
            f.write("id,value\n")
            for i in range(rows_per_file):
                f.write(f"{i},{(i * (r + 1)) % 1000}\n")

        table = petl.fromcsv(str(source))
        table = petl.convert(table, "value", int)
        table = petl.selectgt(table, "value", 250)
        petl.tocsv(table, str(target))


def test_memory_usage_under_bulk_fromdicts_workload(tmp_path: Path) -> None:
    """Ensure repeated fromdicts-based pipelines stay within a coarse memory bound."""
    tracemalloc.start()

    _bulk_fromdicts_and_transforms()

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    max_allowed_bytes = 200 * 1024 * 1024
    assert peak < max_allowed_bytes


def test_memory_usage_under_csv_roundtrip_workload(tmp_path: Path) -> None:
    """Ensure repeated CSV roundtrips do not cause unbounded memory growth."""
    tracemalloc.start()

    _bulk_csv_roundtrips(tmp_path)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    max_allowed_bytes = 200 * 1024 * 1024
    assert peak < max_allowed_bytes
