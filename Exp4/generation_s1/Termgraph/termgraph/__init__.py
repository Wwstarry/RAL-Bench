"""
A small, pure-Python terminal charting library providing a subset of the
reference termgraph project's core public API.

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

__version__ = "0.1.0"