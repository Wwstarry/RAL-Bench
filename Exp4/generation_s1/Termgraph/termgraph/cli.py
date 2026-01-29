from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .args import Args
from .charts import BarChart, StackedChart
from .data import Data


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="termgraph", add_help=True)
    p.add_argument("--width", type=int, default=50)
    p.add_argument("--stacked", action="store_true")
    p.add_argument("--different-scale", action="store_true")
    p.add_argument("--no-labels", action="store_true")
    p.add_argument("--no-values", action="store_true")
    p.add_argument("--format", dest="format", default="{:.2f}")
    p.add_argument("--suffix", default="")
    p.add_argument("--title", default=None)
    p.add_argument("--color", nargs="*", default=None)
    p.add_argument("labels", nargs="*", help="Labels (space separated). Values read from stdin as rows of numbers.")

    ns = p.parse_args(argv)

    # Minimal stdin parsing: whitespace-separated rows, each row is a series list for one label.
    raw = sys.stdin.read().strip()
    rows: List[List[float]] = []
    if raw:
        for line in raw.splitlines():
            line = line.strip()
            if not line:
                continue
            rows.append([float(tok) for tok in line.split()])

    labels = ns.labels if ns.labels else [str(i + 1) for i in range(len(rows))]
    data = Data(labels=labels, values=rows)

    args = Args(
        width=ns.width,
        stacked=ns.stacked,
        different_scale=ns.different_scale,
        no_labels=ns.no_labels,
        no_values=ns.no_values,
        format=ns.format,
        suffix=ns.suffix,
        title=ns.title,
        color=ns.color,
    )

    chart = StackedChart(data, args) if ns.stacked else BarChart(data, args)
    chart.draw()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())