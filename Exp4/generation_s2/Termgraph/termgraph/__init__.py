"""
Pure-Python, minimal terminal charting library compatible with core pieces of
the reference 'termgraph' project.

Public API:
- Data (termgraph.data)
- Args (termgraph.args)
- BarChart, StackedChart (termgraph.charts)
"""
from .data import Data
from .args import Args
from .charts import BarChart, StackedChart

__all__ = ["Data", "Args", "BarChart", "StackedChart"]