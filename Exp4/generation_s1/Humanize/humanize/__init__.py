"""
A small, pure-Python subset of the `humanize` project API.

This implementation is intended to be compatible with the core parts used by
common black-box tests: number formatting, filesize, and time deltas, plus a
minimal i18n layer.
"""

from __future__ import annotations

from .number import intcomma, ordinal
from .filesize import naturalsize
from .time import precisedelta, naturaldelta, naturaltime
from .i18n import activate, deactivate, get_translation, gettext, ngettext

_ = gettext

__version__ = "0.0.0"

__all__ = [
    "intcomma",
    "ordinal",
    "naturalsize",
    "precisedelta",
    "naturaldelta",
    "naturaltime",
    "activate",
    "deactivate",
    "get_translation",
    "gettext",
    "ngettext",
    "_",
    "__version__",
]