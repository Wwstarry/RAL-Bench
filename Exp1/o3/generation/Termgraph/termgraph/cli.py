"""
A *tiny* command-line front-end.  The black-box tests focus on the library API,
but packaging tools and curious users expect a ``python -m termgraph`` entry
point that does *something* reasonable.
"""
from __future__ import annotations

import argparse
import sys

from .args import Args
from .data import Data
from .charts import BarChart, StackedChart


def _parse_cli(argv):
    p = argparse.ArgumentParser(prog="termgraph", description="Simple terminal charts (minimal re-implementation)")

    p.add_argument("numbers", nargs="+", help="numbers to plot (e.g. 3 10 5)")
    p.add_argument("-l", "--label", dest="labels", nargs="*", help="labels for each number")
    p.add_argument("-w", "--width", type=int, default=50, help="chart width")
    p.add_argument("-s", "--stacked", action="store_true", help="stacked chart")
    p.add_argument("-n", "--no-values", action="store_true", dest="no_values", help="hide numeric values")

    return p.parse_args(argv)


def _coerce_numbers(raw):
    try:
        return [float(x) for x in raw]
    except ValueError:
        sys.exit("All numbers must be numeric.")


def main(argv=None):
    ns = _parse_cli(argv or sys.argv[1:])

    numbers = _coerce_numbers(ns.numbers)
    labels = ns.labels or [str(idx + 1) for idx in range(len(numbers))]

    data = Data(labels, [numbers])
    args = Args(width=ns.width, stacked=ns.stacked, no_values=ns.no_values)

    chart_cls = StackedChart if args.stacked else BarChart
    chart = chart_cls(data, args)
    chart.draw()


if __name__ == "__main__":  # pragma: no cover
    main()