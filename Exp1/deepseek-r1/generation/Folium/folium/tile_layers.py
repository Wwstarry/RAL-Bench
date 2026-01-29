from .base import Element

class TileLayer(Element):
    """Tile layer for Leaflet maps."""
    def __init__(self, tiles='OpenStreetMap'):
        super().__init__()
        self.tiles = tiles

    def _render_js(self, map_name):
        """Generate JavaScript for tile layer."""
        url_template = {
            'OpenStreetMap': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        }.get(self.tiles, self.tiles)
        return f'L.tileLayer("{url_template}").addTo({map_name});'

    def render(self):
        return ''