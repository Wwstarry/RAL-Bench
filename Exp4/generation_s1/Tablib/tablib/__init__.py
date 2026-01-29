"""
A tiny, pure-Python subset of the Tablib API required by the test harness.

This is not the full Tablib project. It provides compatible core behavior for
Dataset and Databook, plus CSV/JSON import/export.
"""

from .core import Dataset, Databook

__all__ = ["Dataset", "Databook"]

__version__ = "0.1.0"