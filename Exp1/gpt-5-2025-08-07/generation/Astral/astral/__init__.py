"""
A lightweight pure-Python implementation of core Astral APIs.

Provides:
- LocationInfo: Represents a location with name, region, timezone, latitude, longitude.
- Observer: Simple container for latitude, longitude, elevation.
- sun: Module with functions for dawn, sunrise, solar noon, sunset, dusk times.
- moon: Module with lunar phase calculation.
"""
from .location import LocationInfo, Observer
from . import sun, moon

__all__ = ["LocationInfo", "Observer", "sun", "moon"]