import os
import sys
from pathlib import Path

import psutil  # type: ignore

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


def _memory_mb() -> float:
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def test_memory_usage_for_large_tables():
    rows = [
        [f"row-{i}", i, i * 0.1234, f"value-{i % 10}"]
        for i in range(5000)
    ]
    headers = ["name", "index", "metric", "tag"]

    before = _memory_mb()

    # Call tabulate several times to exercise allocations.
    out1 = tabulate(rows, headers=headers, tablefmt="simple")
    out2 = tabulate(rows, headers=headers, tablefmt="github")
    out3 = tabulate(rows, headers=headers, tablefmt="grid", showindex=True)

    after = _memory_mb()

    # Basic correctness
    assert isinstance(out1, str)
    assert isinstance(out2, str)
    assert isinstance(out3, str)
    assert "row-0" in out1
    assert "row-4999" in out3

    # We only require that the implementation does not blow up memory usage.
    # The threshold is intentionally generous to be robust across platforms.
    delta = max(0.0, after - before)
    assert delta < 300.0
