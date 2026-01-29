from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Observer:
    """
    Represents an observation point on Earth.

    Attributes:
        latitude (float): Decimal degrees, positive north of the equator and negative south.
        longitude (float): Decimal degrees, positive east of Greenwich, negative west.
        elevation (float): Elevation above sea level in meters. Default is 0.
    """
    latitude: float
    longitude: float
    elevation: float = 0.0


class LocationInfo:
    """
    Represents a named location with timezone, latitude and longitude.
    Designed to be API-compatible with core parts of the Astral project.

    Attributes:
        name (str)
        region (str)
        timezone (str): IANA timezone name (e.g., "Europe/London")
        latitude (float)
        longitude (float)
    """
    def __init__(self, name: str = "", region: str = "", timezone: str = "UTC",
                 latitude: float = 0.0, longitude: float = 0.0):
        self.name = name
        self.region = region
        self.timezone = timezone
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        # Elevation is not always known; default to 0. Kept for compatibility.
        self.elevation: float = 0.0

    def __repr__(self) -> str:
        return (f"LocationInfo(name={self.name!r}, region={self.region!r}, "
                f"timezone={self.timezone!r}, latitude={self.latitude:.6f}, "
                f"longitude={self.longitude:.6f})")

    @property
    def observer(self) -> Observer:
        """
        Returns an Observer with this location's latitude, longitude and elevation.
        """
        return Observer(self.latitude, self.longitude, self.elevation)