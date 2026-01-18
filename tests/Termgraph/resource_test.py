from __future__ import annotations

import os
import sys
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
    """Create an Args instance with defaults for resource / integration tests."""
    base: dict = {
        "title": "Normalized Stats",
        "width": 30,
        "format": "{:>4.1f}",
        "suffix": "",
        "no_labels": False,
        "no_values": False,
        "colors": None,
    }
    base.update(overrides)
    kwargs = {k: v for k, v in base.items() if v is not None}
    return Args(**kwargs)  # type: ignore[arg-type]


def test_pipeline_generate_and_render() -> None:
    """Integration-like test: data processing pipeline feeding termgraph."""
    raw_values = [10, 20, 15, 5]
    labels = [f"Item-{i}" for i in range(len(raw_values))]

    # Simple normalization step
    max_val = max(raw_values)
    normalized = [[v / max_val * 10.0] for v in raw_values]

    data = Data(normalized, labels)
    args = _make_args()

    chart = BarChart(data, args)
    chart.draw()
