"""
A lightweight, pure-Python humanization library with a subset of the public API
compatible with the core parts of the reference 'humanize' project.

Top-level helpers:
- number formatting: intcomma, ordinal
- file sizes: naturalsize
- time deltas: precisedelta, naturaldelta, naturaltime
"""

from .number import intcomma, ordinal
from .filesize import naturalsize
from .time import precisedelta, naturaldelta, naturaltime
from . import i18n as i18n  # re-export module for API compatibility

__all__ = [
    "intcomma",
    "ordinal",
    "naturalsize",
    "precisedelta",
    "naturaldelta",
    "naturaltime",
    "i18n",
]

# A simple version string; not strictly necessary for functionality but often expected.
__version__ = "0.1.0"