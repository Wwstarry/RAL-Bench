"""
A very small subset of Textualize's *Rich* library that implements just enough
features for the educational / testing environment used by this course.

Only a fraction of Rich’s huge feature-set is included – just the parts that
are touched by the unit-tests shipped with the assignments.  The public API
mirrors the real Rich project so that existing code can simply replace the
dependency with this light-weight pure-python variant.
"""

from __future__ import annotations

# Public API re-exports
from .console import Console
from .progress import Progress, Task, track
from .table import Table, Column, Row
from .text import Text
from .theme import Theme

__all__ = [
    # Console
    "Console",
    # Table related
    "Table",
    "Column",
    "Row",
    # Progress
    "Progress",
    "Task",
    "track",
    # Text / theme
    "Text",
    "Theme",
]