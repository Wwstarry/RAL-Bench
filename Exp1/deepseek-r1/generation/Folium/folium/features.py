from .base import Element

class Marker(Element):
    """Leaflet marker with popup."""
    def __init__(self, location, popup=None):
        super().__init__()
        self.location = location
        self.popup = popup

    def _render_js(self, map_name):
        """Generate JavaScript for marker."""
        js = f'var {self.get_name()} = L.marker({self.location}).addTo({map_name});'
        if self.popup:
            js += f'{self.get_name()}.bindPopup("{self.popup}");'
        return js

    def render(self):
        """Marker doesn't produce HTML, only JS via parent."""
        return ''

class CircleMarker(Element):
    """Leaflet circle marker."""
    def __init__(self, location, radius=10, color='blue', fill=True):
        super().__init__()
        self.location = location
        self.radius = radius
        self.color = color
        self.fill = fill

    def _render_js(self, map_name):
        """Generate JavaScript for circle marker."""
        options = f'{{radius: {self.radius}, color: "{self.color}", fill: {str(self.fill).lower()}}}'
        return f'var {self.get_name()} = L.circleMarker({self.location}, {options}).addTo({map_name});'

    def render(self):
        return ''

class GeoJson(Element):
    """GeoJSON layer for Leaflet."""
    def __init__(self, data):
        super().__init__()
        self.data = data

    def _render_js(self, map_name):
        """Generate JavaScript for GeoJSON layer."""
        return f'var {self.get_name()} = L.geoJSON({self.data}).addTo({map_name});'

    def render(self):
        return ''