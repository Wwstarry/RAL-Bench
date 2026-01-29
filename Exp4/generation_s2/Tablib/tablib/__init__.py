"""
A small, pure-Python subset of the Tablib API sufficient for the test suite.

Public API:
- Dataset
- Databook
"""

from .core import Dataset, Databook

__all__ = ["Dataset", "Databook"]

# A minimal version marker (not required, but some code expects it to exist).
__version__ = "0.0.0"