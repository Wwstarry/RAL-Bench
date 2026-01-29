"""
A small, pure-Python subset of the Rich library.

This project implements a compatible surface for common usage patterns:
- Console printing with basic markup, emoji replacement, wrapping.
- Table rendering (borders, padding, alignment).
- Progress rendering with deterministic textual output.
- Text objects for styled content.
- Themes (minimal).
"""

from .console import Console
from .table import Table, Column, Row
from .progress import Progress, Task
from .text import Text
from .theme import Theme

__all__ = [
    "Console",
    "Table",
    "Column",
    "Row",
    "Progress",
    "Task",
    "Text",
    "Theme",
]

__version__ = "0.0.0"