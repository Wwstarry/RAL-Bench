class Observer:
    """Represents the location of an observer on Earth."""
    
    def __init__(self, latitude, longitude, elevation=0):
        self.latitude = latitude
        self.longitude = longitude
        self.elevation = elevation

class LocationInfo:
    """Provides information about a location on Earth."""
    
    def __init__(self, name, region, timezone, latitude, longitude):
        """Initializes a LocationInfo object.
        
        Args:
            name: The name of the location
            region: The region of the location
            timezone: The timezone of the location
            latitude: The latitude of the location in degrees
            longitude: The longitude of the location in degrees
        """
        self.name = name
        self.region = region
        self.timezone = timezone
        self.latitude = latitude
        self.longitude = longitude
        self.observer = Observer(latitude, longitude)