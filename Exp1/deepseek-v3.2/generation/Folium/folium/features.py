"""
Feature classes for adding layers and controls to maps.
"""

import json
from typing import Optional, Dict, Any, List
from folium.map import Map


class Feature:
    """Base class for all map features."""
    
    def __init__(self):
        self._parent = None
        self._name = "feature"
    
    def add_to(self, parent):
        """Add this feature to a parent element."""
        parent.add_child(self)
        return self
    
    def get_name(self):
        """Return the name of this feature."""
        return self._name
    
    def _render_js(self):
        """Render JavaScript code for this feature."""
        return ""


class TileLayer(Feature):
    """Tile layer for base maps."""
    
    def __init__(
        self,
        tiles: str = "OpenStreetMap",
        attr: Optional[str] = None,
        name: Optional[str] = None,
        overlay: bool = False,
        control: bool = True,
        **kwargs
    ):
        """
        Initialize a tile layer.
        
        Parameters
        ----------
        tiles : str, default "OpenStreetMap"
            Tile layer URL or provider name.
        attr : str, optional
            Attribution text.
        name : str, optional
            Layer name for layer control.
        overlay : bool, default False
            Whether this is an overlay layer.
        control : bool, default True
            Whether to show in layer control.
        **kwargs : dict
            Additional options passed to Leaflet tile layer.
        """
        super().__init__()
        self.tiles = tiles
        self.attr = attr or self._get_default_attr(tiles)
        self.name = name or tiles
        self.overlay = overlay
        self.control = control
        self.options = kwargs
        self._name = f"tile_layer_{id(self)}"
    
    def _get_default_attr(self, tiles: str) -> str:
        """Get default attribution for known tile providers."""
        attributions = {
            "OpenStreetMap": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            "CartoDB Positron": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://carto.com/attribution">CARTO</a>',
            "CartoDB DarkMatter": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="https://carto.com/attribution">CARTO</a>',
        }
        return attributions.get(tiles, "")
    
    def _render_js(self):
        """Render JavaScript code for tile layer."""
        url_template = self._get_url_template()
        
        js = f'var {self._name} = L.tileLayer("{url_template}", {{\n'
        
        # Add attribution
        if self.attr:
            js += f'    attribution: "{self.attr}",\n'
        
        # Add other options
        for key, value in self.options.items():
            js += f'    {key}: {json.dumps(value)},\n'
        
        js += '}).addTo(map);\n'
        
        # Store layer info for layer control
        js += f'{self._name}.layer_name = "{self.name}";\n'
        js += f'{self._name}.overlay = {str(self.overlay).lower()};\n'
        js += f'{self._name}.control = {str(self.control).lower()};\n'
        
        return js
    
    def _get_url_template(self):
        """Get URL template for tile layer."""
        templates = {
            "OpenStreetMap": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "CartoDB Positron": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}.png",
            "CartoDB DarkMatter": "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png",
            "Stamen Terrain": "https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
            "Stamen Toner": "https://stamen-tiles-{s}.a.ssl.fastly.net/toner/{z}/{x}/{y}.png",
            "Stamen Watercolor": "https://stamen-tiles-{s}.a.ssl.fastly.net/watercolor/{z}/{x}/{y}.jpg",
        }
        
        if self.tiles in templates:
            return templates[self.tiles]
        
        # Assume it's already a URL template
        return self.tiles


class Marker(Feature):
    """Marker layer for points."""
    
    def __init__(
        self,
        location: List[float],
        popup: Optional[str] = None,
        tooltip: Optional[str] = None,
        icon: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize a marker.
        
        Parameters
        ----------
        location : list of float
            Latitude and longitude of the marker.
        popup : str, optional
            Popup text.
        tooltip : str, optional
            Tooltip text.
        icon : dict, optional
            Icon options.
        **kwargs : dict
            Additional options passed to Leaflet marker.
        """
        super().__init__()
        self.location = location
        self.popup = popup
        self.tooltip = tooltip
        self.icon = icon or {}
        self.options = kwargs
        self._name = f"marker_{id(self)}"
    
    def _render_js(self):
        """Render JavaScript code for marker."""
        js = f'var {self._name} = L.marker({self.location}'
        
        # Add options
        if self.options:
            js += f', {json.dumps(self.options)}'
        
        js += ').addTo(map);\n'
        
        # Add popup
        if self.popup:
            js += f'{self._name}.bindPopup("{self.popup}");\n'
        
        # Add tooltip
        if self.tooltip:
            js += f'{self._name}.bindTooltip("{self.tooltip}");\n'
        
        return js


class CircleMarker(Feature):
    """Circle marker layer."""
    
    def __init__(
        self,
        location: List[float],
        radius: int = 10,
        color: str = "#3388ff",
        fill: bool = True,
        fill_color: Optional[str] = None,
        fill_opacity: float = 0.2,
        weight: int = 2,
        **kwargs
    ):
        """
        Initialize a circle marker.
        
        Parameters
        ----------
        location : list of float
            Latitude and longitude of the circle.
        radius : int, default 10
            Radius in pixels.
        color : str, default "#3388ff"
            Stroke color.
        fill : bool, default True
            Whether to fill the circle.
        fill_color : str, optional
            Fill color (defaults to stroke color).
        fill_opacity : float, default 0.2
            Fill opacity.
        weight : int, default 2
            Stroke width in pixels.
        **kwargs : dict
            Additional options passed to Leaflet circle marker.
        """
        super().__init__()
        self.location = location
        self.radius = radius
        self.color = color
        self.fill = fill
        self.fill_color = fill_color or color
        self.fill_opacity = fill_opacity
        self.weight = weight
        self.options = kwargs
        self._name = f"circle_marker_{id(self)}"
    
    def _render_js(self):
        """Render JavaScript code for circle marker."""
        options = {
            "radius": self.radius,
            "color": self.color,
            "fill": self.fill,
            "fillColor": self.fill_color,
            "fillOpacity": self.fill_opacity,
            "weight": self.weight,
            **self.options
        }
        
        js = f'var {self._name} = L.circleMarker({self.location}, {json.dumps(options)}).addTo(map);\n'
        return js


class GeoJson(Feature):
    """GeoJSON layer."""
    
    def __init__(
        self,
        data: Dict[str, Any],
        name: Optional[str] = None,
        style: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Initialize a GeoJSON layer.
        
        Parameters
        ----------
        data : dict
            GeoJSON data.
        name : str, optional
            Layer name.
        style : dict, optional
            Style options.
        **kwargs : dict
            Additional options passed to Leaflet GeoJSON.
        """
        super().__init__()
        self.data = data
        self.name = name or "GeoJSON"
        self.style = style or {}
        self.options = kwargs
        self._name = f"geojson_{id(self)}"
    
    def _render_js(self):
        """Render JavaScript code for GeoJSON layer."""
        js = f'var {self._name}_data = {json.dumps(self.data)};\n'
        
        options = {**self.options}
        if self.style:
            options["style"] = self.style
        
        js += f'var {self._name} = L.geoJSON({self._name}_data, {json.dumps(options)}).addTo(map);\n'
        
        # Store layer info
        js += f'{self._name}.layer_name = "{self.name}";\n'
        js += f'{self._name}.overlay = true;\n'
        js += f'{self._name}.control = true;\n'
        
        return js


class LayerControl(Feature):
    """Layer control for toggling layers."""
    
    def __init__(self):
        """Initialize a layer control."""
        super().__init__()
        self._name = "layer_control"
    
    def _render_js(self):
        """Render JavaScript code for layer control."""
        js = """
        // Collect layers for control
        var baseLayers = {};
        var overlays = {};
        
        // Find all layers with control flag
        for (var key in window) {
            if (window.hasOwnProperty(key)) {
                var obj = window[key];
                if (obj && obj.layer_name !== undefined && obj.control) {
                    if (obj.overlay) {
                        overlays[obj.layer_name] = obj;
                    } else {
                        baseLayers[obj.layer_name] = obj;
                    }
                }
            }
        }
        
        // Add layer control
        L.control.layers(baseLayers, overlays).addTo(map);
        """
        return js