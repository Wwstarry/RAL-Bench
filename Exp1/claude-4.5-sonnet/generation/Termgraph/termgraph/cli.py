"""
Command-line interface for termgraph
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
        description="Draw basic graphs in the terminal"
    )
    
    parser.add_argument(
        "filename",
        nargs="?",
        help="Data file to read (default: stdin)"
    )
    
    parser.add_argument(
        "--width",
        type=int,
        default=50,
        help="Width of the chart in characters (default: 50)"
    )
    
    parser.add_argument(
        "--stacked",
        action="store_true",
        help="Render as stacked chart"
    )
    
    parser.add_argument(
        "--different-scale",
        action="store_true",
        help="Use different scales for each series"
    )
    
    parser.add_argument(
        "--no-labels",
        action="store_true",
        help="Don't show labels"
    )
    
    parser.add_argument(
        "--format",
        default="{:.2f}",
        help="Format string for numeric values (default: {:.2f})"
    )
    
    parser.add_argument(
        "--suffix",
        default="",
        help="Suffix to append to values"
    )
    
    parser.add_argument(
        "--vertical",
        action="store_true",
        help="Render chart vertically"
    )
    
    parser.add_argument(
        "--histogram",
        action="store_true",
        help="Render as histogram"
    )
    
    parser.add_argument(
        "--no-values",
        action="store_true",
        help="Don't show numeric values"
    )
    
    parser.add_argument(
        "--color",
        nargs="*",
        help="Color configuration"
    )
    
    parser.add_argument(
        "--title",
        help="Chart title"
    )
    
    args = parser.parse_args()
    
    # Read data from file or stdin
    if args.filename:
        with open(args.filename, 'r') as f:
            lines = f.readlines()
    else:
        lines = sys.stdin.readlines()
    
    # Parse data
    labels = []
    data = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        parts = line.split()
        if len(parts) < 2:
            continue
        
        label = parts[0]
        values = [float(x) for x in parts[1:]]
        
        labels.append(label)
        if len(values) == 1:
            data.append(values[0])
        else:
            data.append(values)
    
    # Create Data and Args objects
    chart_data = Data(labels=labels, data=data)
    chart_args = Args(
        width=args.width,
        stacked=args.stacked,
        different_scale=args.different_scale,
        no_labels=args.no_labels,
        format=args.format,
        suffix=args.suffix,
        vertical=args.vertical,
        histogram=args.histogram,
        no_values=args.no_values,
        color=args.color,
        labels=not args.no_labels,
        title=args.title
    )
    
    # Create and draw chart
    if args.stacked:
        chart = StackedChart(chart_data, chart_args)
    else:
        chart = BarChart(chart_data, chart_args)
    
    chart.draw()


if __name__ == "__main__":
    main()