from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from .args import Args
from .charts import BarChart, StackedChart
from .data import Data


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="termgraph", add_help=True)
    p.add_argument("--width", type=int, default=50)
    p.add_argument("--stacked", action="store_true", default=False)
    p.add_argument("--different-scale", action="store_true", default=False)
    p.add_argument("--no-labels", action="store_true", default=False)
    p.add_argument("--format", dest="format", default="{:<5.2f}")
    p.add_argument("--suffix", default="")
    p.add_argument("--vertical", action="store_true", default=False)
    p.add_argument("--histogram", action="store_true", default=False)
    p.add_argument("--no-values", action="store_true", default=False)
    p.add_argument("--color", nargs="*", default=None)
    p.add_argument("--title", default=None)
    p.add_argument("data", nargs="*", help="Pairs of label,value(s). Not fully implemented.")
    return p


def main(argv: Optional[List[str]] = None) -> int:
    # Minimal CLI: primarily to satisfy import/entry expectations.
    parser = build_parser()
    ns = parser.parse_args(argv)

    args = Args(
        width=ns.width,
        stacked=ns.stacked,
        different_scale=ns.different_scale,
        no_labels=ns.no_labels,
        format=ns.format,
        suffix=ns.suffix,
        vertical=ns.vertical,
        histogram=ns.histogram,
        no_values=ns.no_values,
        color=ns.color,
        title=ns.title,
    )

    # Extremely simple stdin format: each line "label v1 v2 ..."
    labels: List[str] = []
    series: List[List[float]] = []
    lines = [ln.rstrip("\n") for ln in sys.stdin.read().splitlines() if ln.strip()]
    rows: List[List[float]] = []
    for ln in lines:
        parts = ln.split()
        if not parts:
            continue
        labels.append(parts[0])
        vals = [float(x) for x in parts[1:]] if len(parts) > 1 else [0.0]
        rows.append(vals)

    if rows:
        n_series = max(len(r) for r in rows)
        series = [[] for _ in range(n_series)]
        for r in rows:
            r2 = list(r) + [0.0] * (n_series - len(r))
            for i in range(n_series):
                series[i].append(r2[i])

    data = Data(labels=labels, series=series)

    chart = StackedChart(data, args) if args.stacked else BarChart(data, args)
    chart.draw()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())