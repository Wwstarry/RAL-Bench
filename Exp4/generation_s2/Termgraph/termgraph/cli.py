from __future__ import annotations

import argparse
import sys
from typing import List

from .args import Args
from .charts import BarChart, StackedChart
from .data import Data


def _parse_csv_numbers(s: str) -> List[float]:
    if not s.strip():
        return []
    parts = [p.strip() for p in s.split(",")]
    return [float(p) for p in parts if p != ""]


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="termgraph", add_help=True)
    p.add_argument("--width", type=int, default=50)
    p.add_argument("--stacked", action="store_true")
    p.add_argument("--different-scale", dest="different_scale", action="store_true")
    p.add_argument("--no-labels", dest="no_labels", action="store_true")
    p.add_argument("--format", dest="format", default="{:<5.2f}")
    p.add_argument("--suffix", default="")
    p.add_argument("--no-values", dest="no_values", action="store_true")
    p.add_argument("--title", default=None)

    # Minimal input: labels and one or more series passed as repeated --series "1,2,3"
    p.add_argument("--labels", default=None, help="Comma-separated labels")
    p.add_argument("--series", action="append", default=None, help="Comma-separated numeric series")
    return p


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    parser = build_parser()
    ns = parser.parse_args(argv)

    labels = None
    if ns.labels is not None:
        labels = [x.strip() for x in str(ns.labels).split(",")]

    series = []
    if ns.series:
        for s in ns.series:
            series.append(_parse_csv_numbers(s))

    data = Data(labels=labels or [], data=series)
    args = Args(
        width=ns.width,
        stacked=ns.stacked,
        different_scale=ns.different_scale,
        no_labels=ns.no_labels,
        format=ns.format,
        suffix=ns.suffix,
        no_values=ns.no_values,
        labels=labels,
        title=ns.title,
    )

    chart = StackedChart(data, args) if args.stacked else BarChart(data, args)
    chart.draw()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())