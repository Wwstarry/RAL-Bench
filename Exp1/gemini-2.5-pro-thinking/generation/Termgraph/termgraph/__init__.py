"""
termgraph - a python library for drawing basic graphs in the terminal
"""

from .args import Args
from .charts import BarChart, StackedChart
from .data import Data

def chart(args, data):
    """
    Convenience function to create and draw a chart based on args.

    This function selects the appropriate chart type (e.g., BarChart or
    StackedChart) based on the provided arguments, instantiates it with
    the given data, and calls its draw() method to render it to stdout.
    """
    if args.stacked:
        chart_obj = StackedChart(data, args)
    else:
        chart_obj = BarChart(data, args)

    chart_obj.draw()