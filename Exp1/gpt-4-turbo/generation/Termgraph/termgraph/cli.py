import sys
from .data import Data
from .args import Args
from .charts import BarChart, StackedChart

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Draw basic terminal bar charts.")
    parser.add_argument('--width', type=int, default=50, help='Width of the chart')
    parser.add_argument('--stacked', action='store_true', help='Draw stacked bar chart')
    parser.add_argument('--different-scale', action='store_true', help='Scale each bar independently')
    parser.add_argument('--no-labels', action='store_true', help='Do not show labels')
    parser.add_argument('--format', type=str, default='{:.2f}', help='Format string for values')
    parser.add_argument('--suffix', type=str, default='', help='Suffix for values')
    parser.add_argument('--vertical', action='store_true', help='Draw vertical chart (not implemented)')
    parser.add_argument('--histogram', action='store_true', help='Draw histogram (not implemented)')
    parser.add_argument('--no-values', action='store_true', help='Do not show values')
    parser.add_argument('--color', nargs='*', default=[], help='Bar colors')
    parser.add_argument('--labels', nargs='*', default=[], help='Override labels')
    parser.add_argument('--title', type=str, default=None, help='Chart title')
    parser.add_argument('datafile', nargs='?', type=str, help='Data file (CSV)')
    args = parser.parse_args()

    # Load data
    if args.datafile:
        with open(args.datafile) as f:
            lines = [line.strip() for line in f if line.strip()]
        labels = []
        data = []
        for line in lines:
            parts = line.split(',')
            labels.append(parts[0])
            data.append([float(x) for x in parts[1:]])
    else:
        # Example data
        labels = ['A', 'B', 'C']
        data = [[3, 2], [5, 1], [2, 4]]

    if args.labels:
        labels = args.labels

    data_obj = Data(labels, data, colors=args.color)
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
        labels=args.labels,
        title=args.title
    )

    if args.stacked:
        chart = StackedChart(data_obj, args_obj)
    else:
        chart = BarChart(data_obj, args_obj)

    chart.draw()

if __name__ == "__main__":
    main()