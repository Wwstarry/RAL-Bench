class Observer:
    def __init__(self, latitude=0.0, longitude=0.0, elevation=0.0):
        """
        Observer location.

        :param latitude: Latitude in degrees (positive North)
        :param longitude: Longitude in degrees (positive East)
        :param elevation: Elevation in meters
        """
        self.latitude = float(latitude)
        self.longitude = float(longitude)
        self.elevation = float(elevation)

    def __repr__(self):
        return f"Observer(latitude={self.latitude}, longitude={self.longitude}, elevation={self.elevation})"