import json
from collections import OrderedDict

from .tile_layer import TileLayer
from .layer_control import LayerControl

class Map:
    def __init__(self, location=None, zoom_start=10, tiles='OpenStreetMap', attr=None, width='100%', height='100%', control_scale=False):
        # Default location: somewhere central if not provided
        if location is None:
            location = [0, 0]
        self.location = location
        self.zoom_start = zoom_start
        self.width = width
        self.height = height
        self.control_scale = control_scale

        self._children = OrderedDict()
        self._children['tile_layer'] = TileLayer(tiles=tiles, attr=attr, name=tiles, overlay=False, control=False)
        self._children['layer_control'] = None  # added later if LayerControl added

    def add_child(self, child):
        # Use child's get_name() as key to avoid duplicates
        self._children[child.get_name()] = child
        return self

    def add_child_layer(self, child):
        # Alias for add_child
        return self.add_child(child)

    def add_layer(self, child):
        # Alias for add_child
        return self.add_child(child)

    def add_child_layer_control(self):
        if self._children.get('layer_control') is None:
            lc = LayerControl()
            self._children['layer_control'] = lc
            self.add_child(lc)
        return self._children['layer_control']

    def get_root(self):
        return self

    def render(self):
        # Compose HTML page with Leaflet.js and all children layers
        html = []
        html.append('<!DOCTYPE html>')
        html.append('<html>')
        html.append('<head>')
        html.append('<meta charset="utf-8" />')
        html.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html.append('<title>Folium Map</title>')
        # Leaflet CSS
        html.append('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" '
                    'integrity="sha256-sA+e2Qm0bXrjvQv+3k6bP0b8Xb+X+6FZ5x0x0v+0z0M=" crossorigin=""/>')
        # Leaflet JS
        html.append('<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js" '
                    'integrity="sha256-o9N1j7kz+2b6Xb+6FZ5x0x0v+0z0M=" crossorigin=""></script>')
        # Plugins CSS/JS if any (MarkerCluster)
        if any(isinstance(child, (self._children['tile_layer'].__class__,)) for child in self._children.values()):
            pass  # no extra plugins here
        if any(child.get_name().startswith('marker_cluster') for child in self._children.values()):
            # Add MarkerCluster CSS/JS
            html.append('<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css" />')
            html.append('<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css" />')
            html.append('<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>')

        html.append('<style>')
        html.append(f'#map {{ width: {self.width}; height: {self.height}; }}')
        html.append('</style>')
        html.append('</head>')
        html.append('<body>')
        html.append('<div id="map"></div>')
        html.append('<script>')
        # Initialize map
        html.append(f'var map = L.map("map", {{center: [{self.location[0]}, {self.location[1]}], zoom: {self.zoom_start}}});')

        # Add layers
        for key, child in self._children.items():
            if child is None:
                continue
            child_js = child._render_js()
            if child_js:
                html.append(child_js)

        # Add control scale if requested
        if self.control_scale:
            html.append('L.control.scale().addTo(map);')

        html.append('</script>')
        html.append('</body>')
        html.append('</html>')
        return '\n'.join(html)