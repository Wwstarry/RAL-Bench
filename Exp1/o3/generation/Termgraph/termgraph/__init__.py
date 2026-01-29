"""
A minimal re-implementation of the most frequently used public interface of the
``termgraph`` project.  Only the API surface that the reference black-box test
suite relies on is provided.

You can import the package and use::

    from termgraph import Data, Args, BarChart, StackedChart
"""
from .data import Data
from .args import Args
from .charts import BarChart, StackedChart

__all__ = [
    "Data",
    "Args",
    "BarChart",
    "StackedChart",
]