"""
A small, pure-Python subset of the Tablib API used by the test suite.

This package exposes:
- tablib.Dataset
- tablib.Databook
"""
from .core import Dataset, Databook

__all__ = ["Dataset", "Databook"]