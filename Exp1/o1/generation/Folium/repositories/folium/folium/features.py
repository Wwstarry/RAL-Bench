"""
Implementation of features: Marker, CircleMarker, GeoJson, LayerControl
"""

import json

class BaseFeature:
    def __init__(self):
        self._parent = None

    def add_to(self, parent):
        parent.add_child(self)

    def render(self):
        """
        Returns a tuple of (script, element) to inject into the page.
        Subclasses should override this method with custom Leaflet code.
        """
        return ("", "")

class Marker(BaseFeature):
    def __init__(self, location=None, popup=None):
        super().__init__()
        self.location = location or [0, 0]
        self.popup = popup

    def render(self):
        script = f"""
            L.marker([{self.location[0]}, {self.location[1]}]).addTo(map)
        """
        if self.popup:
            script += f""".bindPopup("{self.popup}")"""
        script += ";\n"
        return (script, "")

class CircleMarker(BaseFeature):
    def __init__(self, location=None, radius=10, color="blue"):
        super().__init__()
        self.location = location or [0, 0]
        self.radius = radius
        self.color = color

    def render(self):
        script = f"""
            L.circleMarker([{self.location[0]}, {self.location[1]}], {{
                radius: {self.radius},
                color: '{self.color}'
            }}).addTo(map);
        """
        return (script, "")

class GeoJson(BaseFeature):
    def __init__(self, data=None):
        super().__init__()
        self.data = data or {}

    def render(self):
        json_data = json.dumps(self.data)
        script = f"""
            L.geoJSON({json_data}).addTo(map);
        """
        return (script, "")

class LayerControl(BaseFeature):
    def __init__(self):
        super().__init__()

    def render(self):
        # Minimal placeholder for toggling layers
        script = """
            L.control.layers(null, null, { position: 'topright' }).addTo(map);
        """
        return (script, "")