"""
A small, pure-Python subset of the `humanize` project.

This package is intentionally minimal and API-compatible with the core helpers
commonly used in tests: number, time, filesize, lists, and a tiny i18n shim.
"""

from __future__ import annotations

from .number import intcomma, ordinal
from .filesize import naturalsize
from .time import precisedelta, naturaldelta, naturaltime
from .lists import naturallist

__all__ = [
    "intcomma",
    "ordinal",
    "naturalsize",
    "precisedelta",
    "naturaldelta",
    "naturaltime",
    "naturallist",
]

# Version metadata (not necessarily matching upstream, but present for callers/tests)
__version__ = "0.0.0"