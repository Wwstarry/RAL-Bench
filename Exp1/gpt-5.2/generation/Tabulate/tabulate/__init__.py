"""
A small, pure-Python table formatting library compatible with core parts of the
reference 'tabulate' project.

This package exposes:
- tabulate()
- simple_separated_format()
- a 'tabulate.formats' registry with preset formats like 'plain', 'grid', 'pipe'
"""
from .core import tabulate, simple_separated_format  # noqa: F401
from .formats import tabulate_formats  # noqa: F401

__all__ = ["tabulate", "simple_separated_format", "tabulate_formats"]

__version__ = "0.1.0"