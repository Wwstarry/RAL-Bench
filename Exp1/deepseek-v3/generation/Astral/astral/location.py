"""Location information for astronomical calculations."""
import datetime
from typing import Optional, Union

class LocationInfo:
    """Contains information about an observer's location."""
    
    def __init__(
        self,
        name: str = '',
        region: str = '',
        timezone: str = 'UTC',
        latitude: float = 0.0,
        longitude: float = 0.0,
        elevation: float = 0.0
    ):
        self.name = name
        self.region = region
        self.timezone = timezone
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation
    
    @property
    def observer(self):
        """Return observer tuple (latitude, longitude, elevation)."""
        return (self.latitude, self.longitude, self.elevation)
    
    def __repr__(self):
        return (f"LocationInfo(name='{self.name}', region='{self.region}', "
                f"timezone='{self.timezone}', latitude={self.latitude}, "
                f"longitude={self.longitude}, elevation={self.elevation})")