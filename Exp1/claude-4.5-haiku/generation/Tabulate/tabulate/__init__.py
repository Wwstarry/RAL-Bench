"""
Pure Python table-formatting library compatible with Tabulate.
"""

from tabulate.core import tabulate
from tabulate.formats import (
    simple_separated_format,
    get_named_table_format,
    list_formats,
)

__version__ = "0.9.0"
__all__ = [
    "tabulate",
    "simple_separated_format",
    "get_named_table_format",
    "list_formats",
]