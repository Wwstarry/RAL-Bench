"""
Core Map class for creating interactive Leaflet maps.
"""

import json
from typing import Optional, List, Dict, Any


class Map:
    """Create a Leaflet map instance."""
    
    def __init__(
        self,
        location: Optional[List[float]] = None,
        zoom_start: int = 10,
        tiles: str = "OpenStreetMap",
        width: str = "100%",
        height: str = "100%",
        **kwargs
    ):
        """
        Initialize a map.
        
        Parameters
        ----------
        location : list of float, optional
            Latitude and longitude of the map center.
        zoom_start : int, default 10
            Initial zoom level.
        tiles : str, default "OpenStreetMap"
            Tile layer to use.
        width : str, default "100%"
            Width of the map.
        height : str, default "100%"
            Height of the map.
        **kwargs : dict
            Additional options passed to Leaflet map.
        """
        self.location = location or [0, 0]
        self.zoom_start = zoom_start
        self.tiles = tiles
        self.width = width
        self.height = height
        self.options = kwargs
        
        # Internal storage
        self._children = {}
        self._parent = None
        self._html = None
        self._template = None
        
        # Root element
        self._root = _Root()
        self._root.add_child(self)
        
        # Add default tile layer
        if tiles:
            from folium.features import TileLayer
            TileLayer(tiles).add_to(self)
    
    def get_root(self):
        """Return the root element of the map."""
        return self._root
    
    def add_child(self, child, name=None, index=None):
        """Add a child to the map."""
        if name is None:
            name = child.get_name()
        
        if index is None:
            self._children[name] = child
        else:
            # Convert to list for ordered insertion
            children_list = list(self._children.items())
            children_list.insert(index, (name, child))
            self._children = dict(children_list)
        
        child._parent = self
        return self
    
    def add_to(self, parent):
        """Add this map to a parent element."""
        parent.add_child(self)
        return self
    
    def render(self, **kwargs):
        """Render the map as HTML string."""
        return self.get_root().render(**kwargs)
    
    def _repr_html_(self):
        """IPython display representation."""
        return self.render()
    
    def get_name(self):
        """Return the name of this element."""
        return "map"


class _Root:
    """Root element for the map hierarchy."""
    
    def __init__(self):
        self._children = {}
        self._name = "root"
    
    def add_child(self, child, name=None, index=None):
        """Add a child to the root."""
        if name is None:
            name = child.get_name()
        
        if index is None:
            self._children[name] = child
        else:
            children_list = list(self._children.items())
            children_list.insert(index, (name, child))
            self._children = dict(children_list)
        
        child._parent = self
        return self
    
    def render(self, **kwargs):
        """Render the complete HTML document."""
        # Header with Leaflet CSS and JS
        header = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
            <title>Folium Map</title>
            <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
                  integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
                  crossorigin=""/>
            <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
                    integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
                    crossorigin=""></script>
            <style>
                html, body {
                    width: 100%;
                    height: 100%;
                    margin: 0;
                    padding: 0;
                }
                #map {
                    position: absolute;
                    top: 0;
                    bottom: 0;
                    right: 0;
                    left: 0;
                }
            </style>
        </head>
        <body>
        """
        
        # Map container
        body = f'<div id="map" style="width: {self._children["map"].width}; height: {self._children["map"].height};"></div>\n'
        body += '<script>\n'
        
        # Initialize map
        map_obj = self._children["map"]
        body += f'var map = L.map("map").setView({map_obj.location}, {map_obj.zoom_start});\n'
        
        # Add options
        if map_obj.options:
            body += f'L.map("map", {json.dumps(map_obj.options)});\n'
        
        # Render children
        for name, child in self._children.items():
            if name != "map":
                body += child._render_js()
        
        body += '</script>\n'
        
        # Footer
        footer = """
        </body>
        </html>
        """
        
        return header + body + footer
    
    def get_name(self):
        """Return the name of this element."""
        return self._name