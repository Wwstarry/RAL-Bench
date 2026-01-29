from __future__ import annotations

import argparse
from typing import List, Optional

from .data import Data
from .args import Args
from .charts import BarChart, StackedChart


def main(argv: Optional[List[str]] = None) -> int:
    """
    Minimal CLI entry point for compatibility with imports/tests.

    This is intentionally small and not a full reimplementation of the original
    termgraph CLI.
    """
    parser = argparse.ArgumentParser(prog="termgraph", add_help=True)
    parser.add_argument("--width", type=int, default=50)
    parser.add_argument("--stacked", action="store_true")
    parser.add_argument("--different-scale", action="store_true")
    parser.add_argument("--no-labels", action="store_true")
    parser.add_argument("--no-values", action="store_true")
    parser.add_argument("--title", type=str, default=None)
    parser.add_argument("--suffix", type=str, default="")
    parser.add_argument("--format", dest="format_", type=str, default="{:<5.2f}")
    parser.add_argument("values", nargs="*", type=float, help="A simple list of numbers")

    ns = parser.parse_args(argv)

    args = Args(
        width=ns.width,
        stacked=ns.stacked,
        different_scale=ns.different_scale,
        no_labels=ns.no_labels,
        no_values=ns.no_values,
        title=ns.title,
        suffix=ns.suffix,
        format=ns.format_,
    )

    data = Data(labels=None, values=ns.values)
    chart = StackedChart(data, args) if args.stacked else BarChart(data, args)
    chart.draw()
    return 0