import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TARGET = os.environ.get("TABULATE_TARGET", "generated").lower()
if TARGET == "reference":
    REPO_ROOT = ROOT / "repositories" / "python-tabulate"
elif TARGET == "generated":
    REPO_ROOT = ROOT / "generation" / "Tabulate"
else:
    raise RuntimeError(f"Unknown TABULATE_TARGET={TARGET!r}")

sys.path.insert(0, str(REPO_ROOT))

from tabulate import tabulate  # type: ignore  # noqa: E402


def test_large_table_formatting_performance():
    # Build a moderately large table to exercise performance.
    rows = [
        [f"row-{i}", i, i * 0.1234, f"value-{i % 10}"]
        for i in range(2000)
    ]
    headers = ["name", "index", "metric", "tag"]

    start = time.perf_counter()
    text = tabulate(rows, headers=headers, tablefmt="grid", showindex=True)
    elapsed = time.perf_counter() - start

    # Basic correctness checks
    assert isinstance(text, str)
    assert "row-0" in text
    assert "row-1999" in text
    assert "name" in text and "metric" in text

    # No strict time bound here; the raw elapsed time is recorded by
    # measure_reference.py and will be used as a baseline metric.
    assert elapsed >= 0.0
