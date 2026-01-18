from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[2]

target = os.environ.get("TINYDB_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "tinydb"
else:
    REPO_ROOT = ROOT / "generation" / "TinyDB"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tinydb import TinyDB, Query  # type: ignore  # noqa: E402
from tinydb.storages import MemoryStorage  # type: ignore  # noqa: E402


def run_tinydb_performance_benchmark(
    num_docs: int = 5000,
    iterations: int = 10,
) -> Dict[str, float]:
    """
    Populate an in-memory TinyDB and run repeated queries.

    This serves as a black-box performance workload: the benchmark
    can be re-used by the evaluation harness without modification.
    """
    db = TinyDB(storage=MemoryStorage)
    Item = Query()

    # Populate database
    for i in range(num_docs):
        db.insert(
            {
                "name": f"item-{i}",
                "group": i % 10,
                "value": i,
            }
        )

    t0 = time.perf_counter()
    matched = 0
    for _ in range(iterations):
        res = db.search((Item.group == 3) & (Item.value >= 100))
        matched += len(res)
    t1 = time.perf_counter()

    total_time = t1 - t0
    if total_time <= 0.0:
        total_time = 1e-9

    queries = iterations
    queries_per_second = queries / total_time
    docs_per_second = (num_docs * iterations) / total_time

    db.close()

    return {
        "num_docs": float(num_docs),
        "iterations": float(iterations),
        "matched_docs": float(matched),
        "total_time_seconds": float(total_time),
        "queries_per_second": float(queries_per_second),
        "docs_per_second": float(docs_per_second),
    }


def test_tinydb_performance_smoke() -> None:
    """Smoke test to ensure the performance benchmark runs successfully."""
    metrics = run_tinydb_performance_benchmark(num_docs=2000, iterations=5)
    assert metrics["total_time_seconds"] > 0.0
    assert metrics["queries_per_second"] > 0.0
    assert metrics["docs_per_second"] > 0.0
