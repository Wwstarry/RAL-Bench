"""
Location information for astronomical calculations
"""

import datetime
from typing import Optional, Tuple, Union


class LocationInfo:
    """Information about a location for astronomical calculations"""

    __slots__ = ("name", "region", "timezone", "latitude", "longitude", "elevation")

    def __init__(
        self,
        name: str,
        region: str,
        timezone: str,
        latitude: float,
        longitude: float,
        elevation: float = 0,
    ):
        """
        Initialize a LocationInfo object.

        Args:
            name: Name of the location
            region: Region of the location
            timezone: Timezone name (e.g., 'America/New_York')
            latitude: Latitude in decimal degrees (north positive)
            longitude: Longitude in decimal degrees (east positive)
            elevation: Elevation in meters above sea level (default: 0)
        """
        self.name = name
        self.region = region
        self.timezone = timezone
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation

    @property
    def observer(self) -> Tuple[float, float, float]:
        """Get observer coordinates as (latitude, longitude, elevation)"""
        return (self.latitude, self.longitude, self.elevation)

    def __repr__(self) -> str:
        return (
            f"LocationInfo(name={self.name!r}, region={self.region!r}, "
            f"timezone={self.timezone!r}, latitude={self.latitude}, "
            f"longitude={self.longitude}, elevation={self.elevation})"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, LocationInfo):
            return False
        return (
            self.name == other.name
            and self.region == other.region
            and self.timezone == other.timezone
            and abs(self.latitude - other.latitude) < 1e-10
            and abs(self.longitude - other.longitude) < 1e-10
            and abs(self.elevation - other.elevation) < 1e-10
        )