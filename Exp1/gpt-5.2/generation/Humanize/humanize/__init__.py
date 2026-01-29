"""
Pure-Python subset of the `humanize` project.

This implementation aims to be API-compatible with the core parts used by
typical black-box tests: number formatting, file sizes, times, lists, and i18n
activation.
"""

from __future__ import annotations

from .number import intcomma, intword, ordinal, apnumber, fraction, scientific, metric
from .filesize import naturalsize
from .time import naturaldelta, naturaltime, precisedelta
from .lists import natural_list
from . import i18n as i18n

__all__ = [
    # number
    "intcomma",
    "intword",
    "ordinal",
    "apnumber",
    "fraction",
    "scientific",
    "metric",
    # filesize
    "naturalsize",
    # time
    "naturaldelta",
    "naturaltime",
    "precisedelta",
    # lists
    "natural_list",
    # i18n module
    "i18n",
]

__version__ = "0.0.0+purepython"