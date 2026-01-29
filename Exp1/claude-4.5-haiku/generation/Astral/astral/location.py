"""
Location information and observer data.
"""

from dataclasses import dataclass
from typing import Optional
import pytz


@dataclass
class Observer:
    """Observer location with latitude, longitude, and elevation."""
    latitude: float
    longitude: float
    elevation: float = 0.0


@dataclass
class LocationInfo:
    """
    Represents a named location with geographic and timezone information.
    """
    name: str
    region: str
    latitude: float
    longitude: float
    timezone: str
    elevation: float = 0.0

    @property
    def observer(self) -> Observer:
        """Return an Observer object for this location."""
        return Observer(
            latitude=self.latitude,
            longitude=self.longitude,
            elevation=self.elevation
        )

    def tzinfo(self):
        """Return the timezone info object."""
        return pytz.timezone(self.timezone)