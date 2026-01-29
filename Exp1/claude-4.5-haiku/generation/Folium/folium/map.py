"""
Core map and layer classes for Folium.
"""

import json
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union


class Element:
    """Base class for all map elements."""

    def __init__(self):
        self._id = str(uuid.uuid4())
        self._parent = None
        self._children = []

    def get_root(self):
        """Get the root element (typically a Map)."""
        if self._parent is None:
            return self
        return self._parent.get_root()

    def add_child(self, child):
        """Add a child element."""
        if not isinstance(child, Element):
            raise TypeError("Child must be an Element instance")
        child._parent = self
        self._children.append(child)
        return self

    def render(self) -> str:
        """Render the element to HTML/JavaScript."""
        raise NotImplementedError


class Map(Element):
    """
    Create a Leaflet map.
    
    Parameters
    ----------
    location : tuple of float
        Initial geographic center of the map as (latitude, longitude)
    zoom_start : int, default 10
        Initial zoom level
    tiles : str, default "OpenStreetMap"
        Tile provider name
    attr : str, optional
        Attribution string for tiles
    min_zoom : int, default 0
        Minimum zoom level
    max_zoom : int, default 18
        Maximum zoom level
    """

    def __init__(
        self,
        location: Tuple[float, float] = (45.5236, -122.6750),
        zoom_start: int = 10,
        tiles: str = "OpenStreetMap",
        attr: Optional[str] = None,
        min_zoom: int = 0,
        max_zoom: int = 18,
    ):
        super().__init__()
        self.location = location
        self.zoom_start = zoom_start
        self.tiles = tiles
        self.attr = attr
        self.min_zoom = min_zoom
        self.max_zoom = max_zoom
        self._tile_layer = None
        
        # Add default tile layer
        if tiles:
            self._tile_layer = TileLayer(tiles, attr=attr)
            self.add_child(self._tile_layer)

    def render(self) -> str:
        """Render the map to HTML."""
        map_id = f"map_{self._id}"
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '    <meta charset="utf-8" />',
            '    <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css" />',
            '    <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>',
            '    <style>',
            f'        #{map_id} {{ height: 100vh; }}',
            '    </style>',
            '</head>',
            '<body>',
            f'    <div id="{map_id}"></div>',
            '    <script>',
            f'        var map = L.map("{map_id}").setView([{self.location[0]}, {self.location[1]}], {self.zoom_start});',
            f'        map.options.minZoom = {self.min_zoom};',
            f'        map.options.maxZoom = {self.max_zoom};',
        ]
        
        # Render tile layer
        if self._tile_layer:
            html_parts.append(self._tile_layer._render_js(map_id))
        
        # Render children (markers, geojson, etc.)
        for child in self._children:
            if child is not self._tile_layer:
                html_parts.append(child._render_js(map_id))
        
        html_parts.extend([
            '    </script>',
            '</body>',
            '</html>',
        ])
        
        return '\n'.join(html_parts)


class TileLayer(Element):
    """
    Add a tile layer to the map.
    
    Parameters
    ----------
    tiles : str
        Tile provider name (e.g., "OpenStreetMap", "CartoDB positron")
    attr : str, optional
        Attribution string
    """

    TILE_PROVIDERS = {
        "OpenStreetMap": {
            "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        },
        "CartoDB positron": {
            "url": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            "attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        },
        "CartoDB voyager": {
            "url": "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
            "attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        },
    }

    def __init__(self, tiles: str = "OpenStreetMap", attr: Optional[str] = None):
        super().__init__()
        self.tiles = tiles
        
        if tiles in self.TILE_PROVIDERS:
            provider = self.TILE_PROVIDERS[tiles]
            self.url = provider["url"]
            self.attr = attr or provider["attr"]
        else:
            self.url = tiles
            self.attr = attr or ""

    def _render_js(self, map_id: str) -> str:
        """Render JavaScript to add tile layer to map."""
        attr_escaped = self.attr.replace('"', '\\"')
        return f'        L.tileLayer("{self.url}", {{ attribution: "{attr_escaped}" }}).addTo(map);'


class Marker(Element):
    """
    Add a marker to the map.
    
    Parameters
    ----------
    location : tuple of float
        Marker position as (latitude, longitude)
    popup : str, optional
        Popup text
    tooltip : str, optional
        Tooltip text
    """

    def __init__(
        self,
        location: Tuple[float, float],
        popup: Optional[str] = None,
        tooltip: Optional[str] = None,
    ):
        super().__init__()
        self.location = location
        self.popup = popup
        self.tooltip = tooltip

    def _render_js(self, map_id: str) -> str:
        """Render JavaScript to add marker to map."""
        marker_id = f"marker_{self._id}"
        js_lines = [
            f'        var {marker_id} = L.marker([{self.location[0]}, {self.location[1]}]).addTo(map);',
        ]
        
        if self.popup:
            popup_escaped = self.popup.replace('"', '\\"')
            js_lines.append(f'        {marker_id}.bindPopup("{popup_escaped}");')
        
        if self.tooltip:
            tooltip_escaped = self.tooltip.replace('"', '\\"')
            js_lines.append(f'        {marker_id}.bindTooltip("{tooltip_escaped}");')
        
        return '\n'.join(js_lines)


class CircleMarker(Element):
    """
    Add a circle marker to the map.
    
    Parameters
    ----------
    location : tuple of float
        Circle center as (latitude, longitude)
    radius : float, default 5
        Circle radius in pixels
    popup : str, optional
        Popup text
    color : str, default "blue"
        Circle color
    fill : bool, default True
        Whether to fill the circle
    fillColor : str, optional
        Fill color (defaults to color)
    fillOpacity : float, default 0.7
        Fill opacity
    weight : int, default 2
        Border weight in pixels
    opacity : float, default 1.0
        Border opacity
    """

    def __init__(
        self,
        location: Tuple[float, float],
        radius: float = 5,
        popup: Optional[str] = None,
        color: str = "blue",
        fill: bool = True,
        fillColor: Optional[str] = None,
        fillOpacity: float = 0.7,
        weight: int = 2,
        opacity: float = 1.0,
    ):
        super().__init__()
        self.location = location
        self.radius = radius
        self.popup = popup
        self.color = color
        self.fill = fill
        self.fillColor = fillColor or color
        self.fillOpacity = fillOpacity
        self.weight = weight
        self.opacity = opacity

    def _render_js(self, map_id: str) -> str:
        """Render JavaScript to add circle marker to map."""
        circle_id = f"circle_{self._id}"
        options = {
            "radius": self.radius,
            "color": self.color,
            "fill": "true" if self.fill else "false",
            "fillColor": self.fillColor,
            "fillOpacity": self.fillOpacity,
            "weight": self.weight,
            "opacity": self.opacity,
        }
        
        options_str = ", ".join(f'{k}: {v}' for k, v in options.items())
        
        js_lines = [
            f'        var {circle_id} = L.circleMarker([{self.location[0]}, {self.location[1]}], {{{options_str}}}).addTo(map);',
        ]
        
        if self.popup:
            popup_escaped = self.popup.replace('"', '\\"')
            js_lines.append(f'        {circle_id}.bindPopup("{popup_escaped}");')
        
        return '\n'.join(js_lines)


class GeoJson(Element):
    """
    Add a GeoJSON layer to the map.
    
    Parameters
    ----------
    data : dict or str
        GeoJSON data as dict or JSON string
    popup : str, optional
        Popup text
    style : dict, optional
        Style options for features
    """

    def __init__(
        self,
        data: Union[Dict, str],
        popup: Optional[str] = None,
        style: Optional[Dict] = None,
    ):
        super().__init__()
        if isinstance(data, str):
            self.data = json.loads(data)
        else:
            self.data = data
        self.popup = popup
        self.style = style or {}

    def _render_js(self, map_id: str) -> str:
        """Render JavaScript to add GeoJSON to map."""
        geojson_id = f"geojson_{self._id}"
        data_json = json.dumps(self.data)
        
        style_str = ""
        if self.style:
            style_dict = ", ".join(f"'{k}': {json.dumps(v)}" for k, v in self.style.items())
            style_str = f", style: {{{style_dict}}}"
        
        js_lines = [
            f'        var {geojson_id} = L.geoJSON({data_json}{style_str}).addTo(map);',
        ]
        
        if self.popup:
            popup_escaped = self.popup.replace('"', '\\"')
            js_lines.append(f'        {geojson_id}.bindPopup("{popup_escaped}");')
        
        return '\n'.join(js_lines)


class LayerControl(Element):
    """
    Add layer control to the map for toggling layers.
    
    Parameters
    ----------
    position : str, default "topright"
        Position of the control ("topleft", "topright", "bottomleft", "bottomright")
    """

    def __init__(self, position: str = "topright"):
        super().__init__()
        self.position = position
        self.base_layers = {}
        self.overlay_layers = {}

    def add_base_layer(self, layer: Element, name: str):
        """Add a base layer."""
        self.base_layers[name] = layer
        return self

    def add_overlay_layer(self, layer: Element, name: str):
        """Add an overlay layer."""
        self.overlay_layers[name] = layer
        return self

    def _render_js(self, map_id: str) -> str:
        """Render JavaScript to add layer control to map."""
        js_lines = [
            f'        var layerControl = L.control.layers({{}}, {{}}, {{position: "{self.position}"}}).addTo(map);',
        ]
        return '\n'.join(js_lines)