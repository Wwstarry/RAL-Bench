"""
Implementation of raster layers, e.g., TileLayer
"""

from .features import BaseFeature

class TileLayer(BaseFeature):
    def __init__(self, tiles="OpenStreetMap", attr=None):
        super().__init__()
        self.tiles = tiles
        self.attr = attr or "Map data © OpenStreetMap contributors"

    def render(self):
        if self.tiles.lower() == "openstreetmap":
            tile_url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        else:
            # For demonstration, fallback to OSM
            tile_url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"

        script = f"""
            L.tileLayer('{tile_url}', {{
                attribution: '{self.attr}'
            }}).addTo(map);
        """
        return (script, "")