"""
Pure-Python table formatting library compatible with core parts of the
reference `tabulate` project.

Exposes:
  - tabulate()
  - simple_separated_format()
  - preset table formats such as "plain", "grid", "pipe"
"""

from .core import tabulate, simple_separated_format
from .formats import tabulate_formats, TableFormat

__all__ = [
    "tabulate",
    "simple_separated_format",
    "tabulate_formats",
    "TableFormat",
]

__version__ = "0.9.0-purepy"