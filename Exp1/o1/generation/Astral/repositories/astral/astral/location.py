import math

class Observer:
    """
    Simple container for observer location data, matching
    the naming used by the reference Astral.
    """
    def __init__(self, latitude, longitude, elevation=0):
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.elevation = float(elevation)

class LocationInfo:
    """
    Represents a location with name, region, timezone,
    plus an 'observer' attribute for lat/long/elevation.
    """
    def __init__(
        self,
        name="Greenwich",
        region="England",
        timezone="Europe/London",
        latitude=51.4769,
        longitude=0.0005
    ):
        self.name = name
        self.region = region
        self.timezone = timezone
        # Elevation is kept separately if needed, default to 0
        self.observer = Observer(latitude, longitude, 0.0)