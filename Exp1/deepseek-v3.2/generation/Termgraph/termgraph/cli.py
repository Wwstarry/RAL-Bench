"""
Command-line interface for termgraph.
"""

import sys
import argparse
from typing import List
from .data import Data
from .args import Args
from .charts import BarChart, StackedChart


def parse_data(input_lines: List[str]) -> Data:
    """
    Parse input data from lines of text.
    
    Args:
        input_lines: List of input lines
        
    Returns:
        Data object
    """
    labels = []
    data_series = []
    
    for line in input_lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = line.split()
        if not parts:
            continue
        
        # First part is label
        label = parts[0]
        labels.append(label)
        
        # Remaining parts are data values
        values = []
        for part in parts[1:]:
            try:
                # Try to parse as float first, then int
                val = float(part)
                if val.is_integer():
                    val = int(val)
                values.append(val)
            except ValueError:
                print(f"Warning: Could not parse value '{part}' as number", file=sys.stderr)
                values.append(0)
        
        # Add values to appropriate series
        for i, val in enumerate(values):
            if i >= len(data_series):
                data_series.append([])
            data_series[i].append(val)
    
    return Data(labels, data_series)


def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Draw basic graphs on terminal",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Chart dimensions
    parser.add_argument('--width', type=int, default=50,
                       help='width of chart in characters')
    
    # Chart type
    parser.add_argument('--stacked', action='store_true',
                       help='stacked bar chart')
    parser.add_argument('--histogram', action='store_true',
                       help='histogram mode')
    parser.add_argument('--vertical', action='store_true',
                       help='vertical chart')
    
    # Display options
    parser.add_argument('--no-labels', action='store_true',
                       help='disable labels')
    parser.add_argument('--no-values', action='store_true',
                       help='disable values')
    parser.add_argument('--format', type=str, default='{:>5.2f}',
                       help='format specifier for values')
    parser.add_argument('--suffix', type=str, default='',
                       help='suffix for values')
    parser.add_argument('--title', type=str,
                       help='chart title')
    
    # Color options
    parser.add_argument('--color', action='append',
                       help='colors for each series')
    
    # Data scaling
    parser.add_argument('--different-scale', action='store_true',
                       help='use different scales for each series')
    
    # Custom labels
    parser.add_argument('--labels', type=str,
                       help='comma-separated custom labels')
    
    # Input file
    parser.add_argument('file', nargs='?', type=argparse.FileType('r'),
                       default=sys.stdin,
                       help='input data file (default: stdin)')
    
    args = parser.parse_args()
    
    # Parse custom labels if provided
    custom_labels = None
    if args.labels:
        custom_labels = [label.strip() for label in args.labels.split(',')]
    
    # Read and parse input data
    input_lines = args.file.readlines()
    data = parse_data(input_lines)
    
    # Apply custom labels if provided
    if custom_labels and len(custom_labels) == data.num_labels:
        data.labels = custom_labels
    
    # Create Args object
    args_obj = Args(
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
        title=args.title
    )
    
    # Create and draw chart
    if args.stacked:
        chart = StackedChart(data, args_obj)
    else:
        chart = BarChart(data, args_obj)
    
    chart.draw()


if __name__ == '__main__':
    main()