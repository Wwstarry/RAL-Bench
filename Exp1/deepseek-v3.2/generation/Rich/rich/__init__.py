"""
Rich - Python library for rich text and beautiful formatting in the terminal.
"""

__version__ = "1.0.0"

from rich.console import Console
from rich.table import Table, Column, Row
from rich.progress import Progress, Task
from rich.text import Text
from rich.theme import Theme

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