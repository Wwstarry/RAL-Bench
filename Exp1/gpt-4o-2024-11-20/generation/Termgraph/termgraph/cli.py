# termgraph/cli.py

import sys
from .data import Data
from .args import Args
from .charts import BarChart, StackedChart

def main():
    """
    Entry point for the termgraph CLI.
    """
    # Example usage: Parse arguments and render a chart.
    labels = ["A", "B", "C"]
    series = [[5, 10], [3, 7], [8, 12]]
    data = Data(labels, series)

    args = Args(width=40, stacked=True, format="{:.1f}", suffix=" units")

    if args.stacked:
        chart = StackedChart(data, args)
    else:
        chart = BarChart(data, args)

    chart.draw()

if __name__ == "__main__":
    main()