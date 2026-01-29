import json
from .map import Layer
from .utilities import get_name, json_dump, _validate_location

_TILE_PROVIDERS = {
    "OpenStreetMap": {
        "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    },
    "Stamen Terrain": {
        "url": "https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
        "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
    },
}


class TileLayer(Layer):
    """A layer for adding tile providers to a map."""

    _template = """
    L.tileLayer(
        '{url}',
        {{
            "attribution": '{attr}',
            "detectRetina": false,
            "maxNativeZoom": 18,
            "maxZoom": 18,
            "minZoom": 0,
            "noWrap": false,
            "opacity": 1,
            "subdomains": "abc",
            "tms": false
        }}
    ).addTo({map_variable});
    """

    def __init__(self, tiles="OpenStreetMap", attr=None, name=None, overlay=False, control=True):
        super().__init__(name=name, overlay=overlay, control=control)
        self._name = "tile_layer_" + self._id
        if tiles in _TILE_PROVIDERS:
            self.tiles = _TILE_PROVIDERS[tiles]["url"]
            self.attr = attr if attr is not None else _TILE_PROVIDERS[tiles]["attr"]
        else:
            self.tiles = tiles
            self.attr = attr if attr is not None else ""

    def render(self, **kwargs):
        map_variable = self.get_root().get_name()
        return self._template.format(
            url=self.tiles, attr=self.attr, map_variable=map_variable
        )


class Marker(Layer):
    """A marker to be placed on the map."""

    _template = """
    var {variable} = L.marker(
        {location},
        {{
            "draggable": false,
            "icon": new L.Icon.Default()
        }}
    ).addTo({map_variable});
    """

    def __init__(self, location, popup=None, tooltip=None, **kwargs):
        super().__init__(name="marker", **kwargs)
        self._name = "marker_" + self._id
        self.location = _validate_location(location)
        self.popup = popup
        self.tooltip = tooltip

    def render(self, **kwargs):
        map_variable = self.get_root().get_name()
        html = self._template.format(
            variable=self.get_name(),
            location=json.dumps(self.location),
            map_variable=map_variable,
        )
        if self.popup:
            html += f"""
            var popup = L.popup({{ "maxWidth": "100%" }});
            var popup_html = `{self.popup}`;
            popup.setContent(popup_html);
            {self.get_name()}.bindPopup(popup);
            """
        if self.tooltip:
            html += f"""
            {self.get_name()}.bindTooltip(`{self.tooltip}`);
            """
        return html


class CircleMarker(Layer):
    """A circle marker with a fixed radius in pixels."""

    _template = """
    var {variable} = L.circleMarker(
        {location},
        {{
            "radius": {radius},
            "color": '{color}',
            "fill": true,
            "fillColor": '{fill_color}',
            "fillOpacity": {fill_opacity}
        }}
    ).addTo({map_variable});
    """

    def __init__(self, location, radius=10, color="blue", fill_color="blue", fill_opacity=0.6, **kwargs):
        super().__init__(name="circle_marker", **kwargs)
        self._name = "circle_marker_" + self._id
        self.location = _validate_location(location)
        self.radius = radius
        self.color = color
        self.fill_color = fill_color
        self.fill_opacity = fill_opacity

    def render(self, **kwargs):
        map_variable = self.get_root().get_name()
        return self._template.format(
            variable=self.get_name(),
            location=json.dumps(self.location),
            radius=self.radius,
            color=self.color,
            fill_color=self.fill_color,
            fill_opacity=self.fill_opacity,
            map_variable=map_variable,
        )


class GeoJson(Layer):
    """A GeoJSON layer."""

    _template = """
    var {variable} = L.geoJson(
        {data},
        {{
            "style": function(feature) {{ return {{ "color": "black", "weight": 1 }}; }}
        }}
    ).addTo({map_variable});
    """

    def __init__(self, data, name=None, **kwargs):
        super().__init__(name=name, **kwargs)
        self._name = "geo_json_" + self._id
        if isinstance(data, str):
            try:
                self.data = json.loads(data)
            except json.JSONDecodeError:
                # Assume it's a file path
                with open(data) as f:
                    self.data = json.load(f)
        elif isinstance(data, dict):
            self.data = data
        else:
            raise ValueError("GeoJson data must be a dict, string, or file path.")

    def render(self, **kwargs):
        map_variable = self.get_root().get_name()
        return self._template.format(
            variable=self.get_name(),
            data=json_dump(self.data),
            map_variable=map_variable,
        )


class LayerControl(Layer):
    """A layer control to toggle layers on and off."""

    _template = """
    var {variable} = L.control.layers(
        {base_layers},
        {overlay_layers},
        {{
            "collapsed": true,
            "position": "topright"
        }}
    ).addTo({map_variable});
    """

    def __init__(self):
        super().__init__(name="layer_control")
        self._name = "layer_control_" + self._id

    def render(self, **kwargs):
        map_obj = self.get_root()
        map_variable = map_obj.get_name()

        base_layers = {}
        overlay_layers = {}

        for child in map_obj.children.values():
            if isinstance(child, Layer) and child.control:
                if child.overlay:
                    overlay_layers[child.layer_name] = child.get_name()
                else:
                    base_layers[child.layer_name] = child.get_name()
        
        # Create JS-compatible dict strings
        base_layers_str = "{" + ", ".join([f'"{k}": {v}' for k, v in base_layers.items()]) + "}"
        overlay_layers_str = "{" + ", ".join([f'"{k}": {v}' for k, v in overlay_layers.items()]) + "}"

        return self._template.format(
            variable=self.get_name(),
            base_layers=base_layers_str,
            overlay_layers=overlay_layers_str,
            map_variable=map_variable,
        )