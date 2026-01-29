"""
A simplified Python table-formatting library, providing a tabulate() function
and a simple_separated_format() function, along with preset format names such as
'plain', 'grid', 'pipe', etc.

The implementations inside this repository are meant to be compatible with the
common usage patterns of the reference Tabulate library.
"""

from .core import tabulate, simple_separated_format
from .formats import PLAIN, GRID, PIPE, HTML, SIMPLE_SEPARATED

__all__ = [
    "tabulate",
    "simple_separated_format",
    "PLAIN",
    "GRID",
    "PIPE",
    "HTML",
    "SIMPLE_SEPARATED",
]