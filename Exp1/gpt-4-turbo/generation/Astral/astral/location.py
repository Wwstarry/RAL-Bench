# astral/location.py

from datetime import tzinfo
from typing import Optional

class Observer:
    """Represents an observer's position on Earth."""
    def __init__(self, latitude: float, longitude: float, elevation: float = 0.0):
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation

    def __eq__(self, other):
        if not isinstance(other, Observer):
            return False
        return (
            abs(self.latitude - other.latitude) < 1e-9 and
            abs(self.longitude - other.longitude) < 1e-9 and
            abs(self.elevation - other.elevation) < 1e-6
        )

    def __repr__(self):
        return f"Observer(latitude={self.latitude}, longitude={self.longitude}, elevation={self.elevation})"

class LocationInfo:
    """Represents a named location with lat/lon/tz."""
    def __init__(
        self,
        name: str = "",
        region: str = "",
        timezone: Optional[str] = None,
        latitude: float = 0.0,
        longitude: float = 0.0
    ):
        self.name = name
        self.region = region
        self.timezone = timezone
        self.latitude = latitude
        self.longitude = longitude

    @property
    def observer(self):
        # Astral's observer has elevation, but LocationInfo does not, so default to 0.
        return Observer(self.latitude, self.longitude, 0.0)

    def __repr__(self):
        return (
            f"LocationInfo(name={self.name!r}, region={self.region!r}, "
            f"timezone={self.timezone!r}, latitude={self.latitude}, longitude={self.longitude})"
        )