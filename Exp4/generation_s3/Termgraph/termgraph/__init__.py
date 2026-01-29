"""
A small, pure-Python terminal charting library with an API compatible with the
core pieces of the reference `termgraph` project used by the test suite.

Public API:
    - Data
    - Args
    - BarChart
    - StackedChart
"""

from .data import Data
from .args import Args
from .charts import BarChart, StackedChart

__all__ = ["Data", "Args", "BarChart", "StackedChart"]