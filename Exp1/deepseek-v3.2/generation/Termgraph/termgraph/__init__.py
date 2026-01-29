"""
Termgraph - A pure Python terminal charting library.
"""

from .data import Data
from .args import Args
from .charts import BarChart, StackedChart

__version__ = "0.1.0"
__all__ = ["Data", "Args", "BarChart", "StackedChart"]