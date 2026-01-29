import json
from folium.elements import Element

class Marker(Element):
    def __init__(self, location, popup=None, tooltip=None, icon=None):
        super().__init__()
        self.location = location
        self.popup = popup
        self.tooltip = tooltip
        self.icon = icon  # Simplified: ignoring icon object complexity for now

    def to_javascript(self, parent_name):
        js = f"""
            var {self.get_name()} = L.marker(
                {self.location},
                {{}}
            ).addTo({parent_name});
        """
        if self.popup:
            js += f"{self.get_name()}.bindPopup('{self.popup}');"
        if self.tooltip:
            js += f"{self.get_name()}.bindTooltip('{self.tooltip}');"
        return js

class CircleMarker(Element):
    def __init__(self, location, radius=10, color="#3388ff", fill=False, fill_color="#3388ff", fill_opacity=0.2, popup=None):
        super().__init__()
        self.location = location
        self.radius = radius
        self.color = color
        self.fill = fill
        self.fill_color = fill_color
        self.fill_opacity = fill_opacity
        self.popup = popup

    def to_javascript(self, parent_name):
        options = {
            "radius": self.radius,
            "color": self.color,
            "fill": self.fill,
            "fillColor": self.fill_color,
            "fillOpacity": self.fill_opacity,
        }
        js = f"""
            var {self.get_name()} = L.circleMarker(
                {self.location},
                {json.dumps(options)}
            ).addTo({parent_name});
        """
        if self.popup:
            js += f"{self.get_name()}.bindPopup('{self.popup}');"
        return js