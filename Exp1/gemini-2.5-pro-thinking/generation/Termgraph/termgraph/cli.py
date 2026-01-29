import argparse
import sys
from . import chart, Args, Data

def main():
    """Main function for the termgraph command-line interface."""
    parser = argparse.ArgumentParser(description='A simple terminal graphing utility.')
    parser.add_argument('filename', nargs='?', help='Data file to read from (default: stdin)')
    parser.add_argument('--width', type=int, default=50, help='Width of the chart')
    parser.add_argument('--title', type=str, help='Title of the chart')
    parser.add_argument('--format', type=str, default='{:<5.2f}', help='Format specifier for values')
    parser.add_argument('--suffix', type=str, default='', help='Suffix to add to values')
    parser.add_argument('--no-labels', action='store_true', help='Hide labels')
    parser.add_argument('--no-values', action='store_true', help='Hide values')
    parser.add_argument('--stacked', action='store_true', help='Enable stacked bar chart')
    parser.add_argument('--color', nargs='*', help='Colors for the bars (e.g., red blue green)')

    # Add other args for API compatibility, even if not fully implemented in this version
    parser.add_argument('--vertical', action='store_true', help='Vertical chart (not implemented)')
    parser.add_argument('--histogram', action='store_true', help='Histogram (not implemented)')
    parser.add_argument('--different-scale', action='store_true', help='Use different scales for multi-series bar charts (not implemented)')

    cli_args = parser.parse_args()

    # Read data from file or stdin
    try:
        if cli_args.filename:
            with open(cli_args.filename, 'r') as f:
                lines = f.readlines()
        else:
            lines = sys.stdin.readlines()
    except FileNotFoundError:
        print(f"Error: File not found at '{cli_args.filename}'", file=sys.stderr)
        sys.exit(1)

    labels = []
    data = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        parts = line.replace(',', ' ').split()
        if not parts:
            continue

        labels.append(parts[0])
        try:
            data.append([float(x) for x in parts[1:]])
        except ValueError:
            print(f"Warning: Could not parse numeric data on line: '{line}'", file=sys.stderr)
            # Add an empty data row to maintain index alignment with labels
            data.append([])

    # Create Args and Data objects from parsed information
    args_dict = vars(cli_args)
    args_dict.pop('filename', None)

    args = Args(**args_dict)
    chart_data = Data(data=data, labels=labels)

    # Generate and draw the chart
    chart(args, chart_data)

if __name__ == '__main__':
    main()