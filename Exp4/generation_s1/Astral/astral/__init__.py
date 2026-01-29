"""
A small, pure-Python subset of the Astral project's public API.

This package provides:
- astral.LocationInfo
- astral.sun module: sun(), dawn(), sunrise(), noon(), sunset(), dusk()
- astral.moon module: phase()
"""

from .location import LocationInfo, Observer
from .errors import AstralError, SunNeverRisesError, SunNeverSetsError

__all__ = [
    "LocationInfo",
    "Observer",
    "AstralError",
    "SunNeverRisesError",
    "SunNeverSetsError",
]

__version__ = "0.0.0"