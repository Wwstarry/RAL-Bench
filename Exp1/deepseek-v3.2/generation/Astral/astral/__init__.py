"""
Astral - Sun and moon time calculation library
"""

from astral.location import LocationInfo
from astral.sun import (
    dawn,
    daylight,
    dusk,
    golden_hour,
    night,
    noon,
    rahukaalam,
    sunrise,
    sunset,
    sun,
    twilight,
)
from astral.moon import phase

__version__ = "3.2"
__author__ = "Astral Library"

__all__ = [
    "LocationInfo",
    "dawn",
    "daylight",
    "dusk",
    "golden_hour",
    "night",
    "noon",
    "rahukaalam",
    "sunrise",
    "sunset",
    "sun",
    "twilight",
    "phase",
]