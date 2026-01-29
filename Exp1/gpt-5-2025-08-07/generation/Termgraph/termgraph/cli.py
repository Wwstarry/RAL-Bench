import argparse
import sys

from .data import Data
from .args import Args
from .charts import BarChart, StackedChart


def parse_args(argv=None) -> Args:
    parser = argparse.ArgumentParser(prog="termgraph", add_help=True)
    parser.add_argument("--width", type=int, default=50)
    parser.add_argument("--stacked", action="store_true")
    parser.add_argument("--different-scale", action="store_true", dest="different_scale")
    parser.add_argument("--no-labels", action="store_true", dest="no_labels")
    parser.add_argument("--format", type=str, default=None)
    parser.add_argument("--suffix", type=str, default="")
    parser.add_argument("--vertical", action="store_true")
    parser.add_argument("--histogram", action="store_true")
    parser.add_argument("--no-values", action="store_true", dest="no_values")
    parser.add_argument("--color", nargs="*", default=[])
    parser.add_argument("--title", type=str, default=None)
    # The reference project has a --labels flag for certain modes; keep for API compatibility.
    parser.add_argument("--labels", action="store_true")

    ns = parser.parse_args(argv)
    return Args(
        width=ns.width,
        stacked=ns.stacked,
        different_scale=ns.different_scale,
        no_labels=ns.no_labels,
        format=ns.format,
        suffix=ns.suffix,
        vertical=ns.vertical,
        histogram=ns.histogram,
        no_values=ns.no_values,
        color=ns.color,
        labels=ns.labels,
        title=ns.title,
    )


def main(argv=None):
    args = parse_args(argv)

    # Simple CLI for demonstration:
    # Read labels and data from stdin as lines "label value1 value2 ..."
    labels = []
    series = []
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        label = parts[0]
        values = [float(x) for x in parts[1:]] if len(parts) > 1 else [0.0]
        labels.append(label)
        series.append(values)

    data = Data(labels, series)

    chart_cls = StackedChart if args.stacked else BarChart
    chart = chart_cls(data, args)
    chart.draw()


if __name__ == "__main__":
    main()