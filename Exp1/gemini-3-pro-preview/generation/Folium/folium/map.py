from folium.elements import Element, Figure
from folium.raster_layers import TileLayer

class Map(Element):
    def __init__(self, location=None, zoom_start=10, tiles="OpenStreetMap"):
        super().__init__()
        self.location = location if location else [0, 0]
        self.zoom_start = zoom_start
        self.tiles = tiles
        
        # Create a Figure if not attached to one, but usually Map is the entry point
        self._parent = Figure()
        self._parent.add_child(self)
        
        # Add default tile layer if requested
        if self.tiles:
            TileLayer(tiles).add_to(self)

    def get_css_links(self):
        return [
            "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css",
            "https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css",
            "https://netdna.bootstrapcdn.com/bootstrap/3.0.0/css/bootstrap.min.css",
            "https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.2.0/css/all.min.css"
        ]

    def get_js_links(self):
        return [
            "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js",
            "https://code.jquery.com/jquery-1.12.4.min.js",
            "https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js",
            "https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.js"
        ]

    def to_html(self):
        return f'<div class="folium-map" id="{self.get_name()}" ></div>'

    def to_javascript(self, parent_name):
        # Map doesn't use parent_name, it binds to the DIV id
        return f"""
            var {self.get_name()} = L.map(
                "{self.get_name()}",
                {{
                    center: {self.location},
                    crs: L.CRS.EPSG3857,
                    zoom: {self.zoom_start},
                    zoomControl: true,
                    preferCanvas: false,
                }}
            );
        """