"""
A small, pure-Python terminal charting library compatible with core parts of the
reference `termgraph` project used by the tests.

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

__version__ = "0.0.0"