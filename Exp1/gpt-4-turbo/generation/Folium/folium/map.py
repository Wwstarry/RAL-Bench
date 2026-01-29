import uuid
import json

from .tilelayer import TileLayer

class MacroElement:
    """Base class for all elements that can be rendered into HTML/JS."""
    def __init__(self):
        self._parent = None

    def add_to(self, parent):
        parent.add_child(self)
        return self

    def render(self, **kwargs):
        raise NotImplementedError

    def get_root(self):
        p = self
        while hasattr(p, '_parent') and p._parent is not None:
            p = p._parent
        return p

class Map(MacroElement):
    def __init__(self, location=None, zoom_start=10, tiles='OpenStreetMap', control_scale=False, **kwargs):
        super().__init__()
        self.location = location or [0, 0]
        self.zoom_start = zoom_start
        self.control_scale = control_scale
        self._children = []
        self._id = f"map_{uuid.uuid4().hex[:8]}"
        self._tilelayer = None
        if tiles:
            self._tilelayer = TileLayer(tiles=tiles)
            self.add_child(self._tilelayer)

    def add_child(self, child):
        child._parent = self
        self._children.append(child)
        return self

    def render(self, **kwargs):
        # Compose HTML
        html = []
        html.append('<!DOCTYPE html>')
        html.append('<html>')
        html.append('<head>')
        html.append('<meta charset="utf-8"/>')
        html.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
        html.append('<title>Folium Map</title>')
        html.append('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>')
        html.append('<style>#%s {width: 100%%; height: 100%%; min-height: 400px;}</style>' % self._id)
        html.append('</head>')
        html.append('<body>')
        html.append(f'<div id="{self._id}"></div>')
        html.append('<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>')
        # Plugins scripts
        for child in self._children:
            if hasattr(child, '_get_plugin_scripts'):
                for script in child._get_plugin_scripts():
                    html.append(script)
        html.append('<script>')
        html.append(f'var map = L.map("{self._id}", {{center: {json.dumps(self.location)}, zoom: {self.zoom_start}}});')
        # Render children
        for child in self._children:
            html.append(child.render(map_var='map'))
        html.append('</script>')
        html.append('</body>')
        html.append('</html>')
        return '\n'.join(html)