from __future__ import annotations

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

# Decide whether to test the reference repo or a generated repo.
target = os.environ.get("TERMGRAPH_TARGET", "reference").lower()
if target == "reference":
    REPO_ROOT = ROOT / "repositories" / "termgraph"
else:
    REPO_ROOT = ROOT / "generation" / "Termgraph"

if not REPO_ROOT.exists():
    raise RuntimeError(f"Target repository does not exist: {REPO_ROOT}")

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from termgraph import (  # type: ignore  # noqa: E402
    Data,
    Args,
    BarChart,
)


def _make_args(**overrides) -> Args:
    """Create an Args instance with defaults used in performance tests."""
    base: dict = {
        "title": None,
        "width": 20,
        "format": "{:>4.1f}",
        "suffix": "",
        "no_labels": False,
        "no_values": False,
        "colors": None,
    }
    base.update(overrides)
    kwargs = {k: v for k, v in base.items() if v is not None}
    return Args(**kwargs)  # type: ignore[arg-type]


def test_performance_many_small_charts() -> None:
    """Render many small charts to ensure performance is reasonable."""
    labels = ["A", "B", "C"]
    values = [[1], [2], [3]]

    data = Data(values, labels)
    args = _make_args(width=20)

    start = time.perf_counter()
    for _ in range(200):
        chart = BarChart(data, args)
        chart.draw()
    elapsed = time.perf_counter() - start

    # Loose upper bound to avoid flakiness but still catch very slow code.
    assert elapsed < 5.0
