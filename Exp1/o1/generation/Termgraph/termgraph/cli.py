import sys
from termgraph.data import Data
from termgraph.args import Args
from termgraph.charts import BarChart, StackedChart

def main():
    """
    Basic CLI entry point that demonstrates constructing Data and Args,
    and drawing either a bar or stacked chart.
    To use:
        python -m termgraph.cli bar ...
        python -m termgraph.cli stacked ...
    Currently, argument parsing is minimal and serves only as a demonstration.
    """
    if len(sys.argv) < 2:
        print("Usage: python -m termgraph.cli [bar|stacked] <values...>")
        sys.exit(1)

    chart_type = sys.argv[1]
    try:
        values = [float(x) for x in sys.argv[2:]]
    except ValueError:
        print("Please provide numeric values.")
        sys.exit(1)

    # Quick demonstration:
    # We'll treat each value as a row in a bar chart,
    # or treat them as a single row of stacked data in a stacked chart.
    if chart_type == 'bar':
        labels = [f"Row {i}" for i in range(len(values))]
        data = Data(labels=labels, data=[[v] for v in values])
        args = Args()  # Use defaults
        BarChart(data, args).draw()
    elif chart_type == 'stacked':
        labels = ["Stacked Row"]
        data = Data(labels=labels, data=[values])
        args = Args(stacked=True)
        StackedChart(data, args).draw()
    else:
        print("Unknown chart type. Choose 'bar' or 'stacked'")