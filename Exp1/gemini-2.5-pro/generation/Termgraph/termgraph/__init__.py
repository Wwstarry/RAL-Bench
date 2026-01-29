"""
termgraph - a python library for drawing basic graphs in the terminal
"""

__version__ = "0.1.0"

from .data import Data
from .args import Args
from .charts import BarChart, StackedChart

def chart(args, data):
    """
    A simple entry point function that creates and draws a chart.
    This function is provided for API compatibility with the original termgraph.
    """
    if args.stacked:
        chart_obj = StackedChart(data, args)
    else:
        chart_obj = BarChart(data, args)
    chart_obj.draw()