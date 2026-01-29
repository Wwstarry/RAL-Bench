"""
A small, pure-Python subset of the `humanize` project.

This repository implements the core APIs used by typical black-box tests:
- number helpers: intcomma, ordinal
- filesize: naturalsize
- time helpers: precisedelta, naturaldelta, naturaltime
- lists: natural_list
- i18n: basic activation/deactivation hooks (no external deps)
"""

from __future__ import annotations

from .number import intcomma, ordinal
from .filesize import naturalsize
from .time import precisedelta, naturaldelta, naturaltime

__all__ = [
    "intcomma",
    "ordinal",
    "naturalsize",
    "precisedelta",
    "naturaldelta",
    "naturaltime",
]

# Convenience re-export for compatibility with some callers.
from .lists import natural_list  # noqa: E402

__all__.append("natural_list")

# i18n module is importable as humanize.i18n
from . import i18n  # noqa: E402

__all__.append("i18n")

# Version is not mandated, but some environments introspect it.
__version__ = "0.0.0"