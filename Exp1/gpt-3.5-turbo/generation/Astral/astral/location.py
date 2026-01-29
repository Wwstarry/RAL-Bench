from dataclasses import dataclass
from typing import Optional
import zoneinfo

@dataclass
class Observer:
    latitude: float
    longitude: float
    elevation: float = 0.0

class LocationInfo:
    """
    Represents a location with a name, region, latitude, longitude, elevation and timezone.
    """
    def __init__(self, name: str = "", region: str = "", latitude: float = 0.0, longitude: float = 0.0, timezone: Optional[str] = None, elevation: float = 0.0):
        self.name = name
        self.region = region
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation
        if timezone is None:
            self.timezone = None
        else:
            # Accept string or zoneinfo.ZoneInfo
            if isinstance(timezone, str):
                self.timezone = zoneinfo.ZoneInfo(timezone)
            else:
                self.timezone = timezone

    @property
    def observer(self) -> Observer:
        return Observer(self.latitude, self.longitude, self.elevation)