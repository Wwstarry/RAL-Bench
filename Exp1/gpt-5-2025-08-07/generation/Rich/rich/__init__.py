# Minimal Rich-compatible public API

from .console import Console
from .table import Table, Column, Row
from .progress import Progress, Task, track

# Lazy optional imports for API compatibility
try:
    from .text import Text
except Exception:  # pragma: no cover
    Text = None  # type: ignore

try:
    from .theme import Theme
except Exception:  # pragma: no cover
    Theme = None  # type: ignore

__all__ = [
    "Console",
    "Table",
    "Column",
    "Row",
    "Progress",
    "Task",
    "Text",
    "Theme",
    "track",
]