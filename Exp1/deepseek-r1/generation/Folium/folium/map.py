from .base import Element
import json

class Map(Element):
    """Main map class for creating Leaflet maps."""
    def __init__(self, location=None, zoom_start=10, tiles='OpenStreetMap', width='100%', height='100%'):
        super().__init__()
        self.location = location or [0, 0]
        self.zoom_start = zoom_start
        self.width = width
        self.height = height
        self.tile_layer = None
        if tiles:
            self.tile_layer = TileLayer(tiles).add_to(self)

    def get_root(self):
        """Return root element (self for Map)."""
        return self

    def render(self):
        """Generate HTML containing Leaflet map and layers."""
        html = []
        # Map container div
        html.append(f'<div id="{self.get_name()}" style="width:{self.width}; height:{self.height}"></div>')
        
        # JavaScript initialization
        script = []
        script.append(f'var {self.get_name()} = L.map("{self.get_name()}").setView({self.location}, {self.zoom_start});')
        
        # Render children (layers)
        for child in self._children.values():
            html.append(child.render())
            script.append(child._render_js(self.get_name()))
        
        # Combine scripts
        html.append(f'<script>{"".join(script)}</script>')
        return '\n'.join(html)