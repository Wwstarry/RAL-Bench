"""Minimal Astral-compatible API for sun and moon calculations (pure Python).

This is not the full Astral project. It implements the small subset of the
public API required by the test suite for this kata.
"""

from .location import LocationInfo
from .types import Observer

__all__ = ["LocationInfo", "Observer"]