"""
Command-line interface for termgraph.
"""

import sys
import argparse
from termgraph.data import Data
from termgraph.args import Args
from termgraph.charts import BarChart, StackedChart


def main():
    """
    Main entry point for the termgraph CLI.
    """
    parser = argparse.ArgumentParser(
        description="A pure Python terminal charting library"
    )
    parser.add_argument(
        "--width",
        type=int,
        default=50,
        help="Width of the chart in characters",
    )
    parser.add_argument(
        "--stacked",
        action="store_true",
        help="Render stacked bars",
    )
    parser.add_argument(
        "--no-labels",
        action="store_true",
        help="Hide row labels",
    )
    parser.add_argument(
        "--no-values",
        action="store_true",
        help="Hide numeric values",
    )
    parser.add_argument(
        "--format",
        default="{:.0f}",
        help="Format string for numeric values",
    )
    parser.add_argument(
        "--suffix",
        default="",
        help="Suffix to append to numeric values",
    )
    parser.add_argument(
        "--title",
        help="Title for the chart",
    )
    
    args = parser.parse_args()
    
    # Example usage - would normally read from stdin or file
    data = Data(
        labels=["A", "B", "C"],
        series=[[10, 20], [15, 25], [20, 30]],
    )
    
    chart_args = Args(
        width=args.width,
        stacked=args.stacked,
        no_labels=args.no_labels,
        no_values=args.no_values,
        format=args.format,
        suffix=args.suffix,
        title=args.title,
    )
    
    if args.stacked:
        chart = StackedChart(data, chart_args)
    else:
        chart = BarChart(data, chart_args)
    
    chart.draw()


if __name__ == "__main__":
    main()