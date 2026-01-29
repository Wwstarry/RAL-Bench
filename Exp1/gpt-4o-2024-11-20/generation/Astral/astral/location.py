from dataclasses import dataclass

@dataclass
class Observer:
    """Represents an observer's location."""
    latitude: float
    longitude: float
    elevation: float = 0.0  # Default elevation is 0 meters.

@dataclass
class LocationInfo:
    """Represents a named location with latitude, longitude, and timezone."""
    name: str
    region: str
    latitude: float
    longitude: float
    timezone: str

    @property
    def observer(self) -> Observer:
        """Returns an Observer object for this location."""
        return Observer(latitude=self.latitude, longitude=self.longitude)