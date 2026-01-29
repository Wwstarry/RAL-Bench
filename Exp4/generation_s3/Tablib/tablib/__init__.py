"""
A minimal, pure-Python subset of the Tablib API required by the test suite.

This is not the full Tablib project; it implements only core Dataset/Databook
functionality and CSV/JSON import/export.
"""

from .core import Dataset, Databook

__all__ = ["Dataset", "Databook"]

# Optional metadata
__version__ = "0.0.0"