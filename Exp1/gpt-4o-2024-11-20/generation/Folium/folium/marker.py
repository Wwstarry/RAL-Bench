class Marker:
    def __init__(self, location, popup=None):
        self.location = location
        self.popup = popup

    def render(self):
        popup = f", {{popup: '{self.popup}'}}" if self.popup else ""
        return f"L.marker({self.location}{popup}).addTo(map);"


class CircleMarker:
    def __init__(self, location, radius=10, color="blue"):
        self.location = location
        self.radius = radius
        self.color = color

    def render(self):
        return f"L.circleMarker({self.location}, {{radius: {self.radius}, color: '{self.color}'}}).addTo(map);"