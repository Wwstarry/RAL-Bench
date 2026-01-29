"""
Location information for astronomical calculations.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class Observer:
    """Represents an observer's position on Earth."""
    latitude: float
    longitude: float
    elevation: float = 0.0


class LocationInfo:
    """Information about a location for astronomical calculations."""
    
    def __init__(
        self,
        name: str = "Greenwich",
        region: str = "England",
        timezone: str = "Europe/London",
        latitude: float = 51.4733,
        longitude: float = -0.0008333,
    ):
        self.name = name
        self.region = region
        self.timezone = timezone
        self.latitude = latitude
        self.longitude = longitude
        self._observer = Observer(latitude=latitude, longitude=longitude, elevation=0.0)
    
    @property
    def observer(self) -> Observer:
        """Return an Observer object for this location."""
        return self._observer