import sys
from .data import Data
from .args import Args
from .charts import BarChart, StackedChart

def main():
    import argparse

    parser = argparse.ArgumentParser(description='termgraph - terminal graph plotting')
    parser.add_argument('file', nargs='?', type=argparse.FileType('r'), default=sys.stdin,
                        help='Input data file (default: stdin)')
    parser.add_argument('--width', type=int, default=50, help='Width of the graph')
    parser.add_argument('--stacked', action='store_true', help='Stacked bar chart')
    parser.add_argument('--different-scale', action='store_true', help='Different scale per series (not implemented)')
    parser.add_argument('--no-labels', action='store_true', help='Do not print labels')
    parser.add_argument('--format', default='{:<5.2f}', help='Format string for values')
    parser.add_argument('--suffix', default='', help='Suffix for values')
    parser.add_argument('--vertical', action='store_true', help='Vertical bars (not implemented)')
    parser.add_argument('--histogram', action='store_true', help='Histogram mode (not implemented)')
    parser.add_argument('--no-values', action='store_true', help='Do not print values')
    parser.add_argument('--title', default=None, help='Title of the chart')
    parser.add_argument('--labels', nargs='*', default=None, help='Override labels')

    args = parser.parse_args()

    # Parse input data
    labels = []
    data = []

    # Read lines, skip empty and comment lines
    lines = [line.strip() for line in args.file if line.strip() and not line.strip().startswith('#')]

    # First line: labels or data?
    # If first line contains non-numeric tokens, treat as labels
    # Otherwise, no labels
    if not lines:
        print("No data provided.", file=sys.stderr)
        sys.exit(1)

    first_line_tokens = lines[0].split()
    try:
        # Try to parse first line tokens as floats
        [float(x) for x in first_line_tokens]
        # first line is data
        labels = None
        data_lines = lines
    except ValueError:
        # first line is labels
        labels = first_line_tokens
        data_lines = lines[1:]

    # Parse data lines
    data_rows = []
    for line in data_lines:
        tokens = line.split()
        try:
            row = [float(x) for x in tokens]
            data_rows.append(row)
        except ValueError:
            print(f"Invalid data line: {line}", file=sys.stderr)
            sys.exit(1)

    # Transpose data_rows to series
    # termgraph expects data as list of series, each series is list of values per label
    # data_rows is list of rows, each row is list of values per series
    # So transpose rows to columns
    if not data_rows:
        print("No data rows found.", file=sys.stderr)
        sys.exit(1)

    n_cols = max(len(row) for row in data_rows)
    # Pad rows with zeros if needed
    for row in data_rows:
        if len(row) < n_cols:
            row.extend([0.0] * (n_cols - len(row)))

    series = []
    for col_i in range(n_cols):
        col = []
        for row in data_rows:
            col.append(row[col_i])
        series.append(col)

    data_obj = Data(labels=labels, data=series)

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
        labels=args.labels,
        title=args.title,
    )

    if args_obj.title:
        print(args_obj.title)

    if args_obj.stacked:
        chart = StackedChart(data_obj, args_obj)
    else:
        chart = BarChart(data_obj, args_obj)

    chart.draw()