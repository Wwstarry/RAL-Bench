from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Observer:
    """Represents an observer on Earth.

    Fields match Astral's core concept: latitude, longitude, elevation (meters).
    """
    latitude: float
    longitude: float
    elevation: float = 0.0