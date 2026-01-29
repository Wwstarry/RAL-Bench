"""
Lightweight local task manager powered by a JSON-based TinyDB-like system.
"""

__version__ = "0.1.0"

from .database import TinyDB, TaskManager
from .queries import where