"""
Pure-Python, lightweight table formatting with an API compatible with the core
of the upstream `tabulate` project.

This package intentionally implements only the subset needed for common usage
and black-box snapshot tests.
"""

from .core import tabulate
from .formats import simple_separated_format, table_formats

__all__ = [
    "tabulate",
    "simple_separated_format",
    "table_formats",
    "tabulate_formats",
]

__version__ = "0.0.0"

# Common compatibility alias: some code/tests expect this name.
tabulate_formats = tuple(table_formats.keys())

# Some tests may look for these names.
formats = table_formats
_table_formats = table_formats