"""
Humanize: utility functions for making numbers more human-readable.

This is a pure Python implementation that is API-compatible with the core
parts of the reference `humanize` project.
"""

__version__ = "4.0.0"

from .i18n import activate, deactivate
from .number import intcomma, ordinal
from .filesize import naturalsize
from .time import naturaldelta, naturaltime, precisedelta

__all__ = [
    "activate",
    "deactivate",
    "intcomma",
    "ordinal",
    "naturalsize",
    "naturaldelta",
    "naturaltime",
    "precisedelta",
    "__version__",
]