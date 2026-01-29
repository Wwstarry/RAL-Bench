# folium/features.py
import json
from folium.map import Layer, FeatureGroup
from folium.elements import Element, Template
from folium.utilities import _validate_location, _to_json, _parse_options

class Marker(Layer):
    """A marker on the map."""
    _template = """
    var {variable} = L.marker(
        {location},
        {options}
    ).addTo({map});
    """
    def __init__(self, location, popup=None, tooltip=None, **kwargs):
        super().__init__()
        self._name = "Marker"
        self.location = _validate_location(location)
        self.popup = popup
        self.tooltip = tooltip
        self.kwargs = kwargs

    def render(self, **kwargs):
        options = _parse_options(**self.kwargs)
        script = Template(self._template).render(
            variable=self.get_name(),
            location=_to_json(self.location),
            options=options,
            map=self._parent.get_name()
        )
        if self.popup:
            script += self._render_popup()
        if self.tooltip:
            script += self._render_tooltip()
        return script
    
    def get_name(self):
        return f"marker_{self._id}"

    def _render_popup(self):
        # A simplified popup implementation
        popup_text = json.dumps(str(self.popup))
        return f"""
        {self.get_name()}.bindPopup({popup_text});
        """

    def _render_tooltip(self):
        tooltip_text = json.dumps(str(self.tooltip))
        return f"""
        {self.get_name()}.bindTooltip({tooltip_text});
        """

class CircleMarker(Marker):
    """A circle marker on the map."""
    _template = """
    var {variable} = L.circleMarker(
        {location},
        {options}
    ).addTo({map});
    """
    def __init__(self, location, radius=10, color='blue', fill_color='blue', **kwargs):
        super().__init__(location, **kwargs)
        self._name = "CircleMarker"
        self.kwargs['radius'] = radius
        self.kwargs['color'] = color
        self.kwargs['fillColor'] = fill_color

    def get_name(self):
        return f"circle_marker_{self._id}"

class GeoJson(Layer):
    """A GeoJSON layer on the map."""
    _template = """
    var {variable} = L.geoJson(
        {data},
        {options}
    ).addTo({map});
    """
    def __init__(self, data, name=None, overlay=True, show=True, **kwargs):
        super().__init__(name=name, overlay=overlay, show=show)
        self._name = "GeoJson"
        if isinstance(data, str):
            try:
                # Check if it's a valid JSON string
                json.loads(data)
                self.data = data
            except json.JSONDecodeError:
                # Assume it's a URL or file path, pass as a JS string literal
                self.data = json.dumps(data)
        else:
            self.data = _to_json(data)
        self.kwargs = kwargs

    def render(self, **kwargs):
        options = _parse_options(**self.kwargs)
        return Template(self._template).render(
            variable=self.get_name(),
            data=self.data,
            options=options,
            map=self._parent.get_name()
        )

    def get_name(self):
        return f"geo_json_{self._id}"

class LayerControl(Element):
    """A layer control to toggle layers on the map."""
    _template = """
    L.control.layers(
        {base_maps},
        {overlay_maps},
        {options}
    ).addTo({map});
    """
    def __init__(self, **kwargs):
        super().__init__()
        self._name = "LayerControl"
        self.kwargs = kwargs

    def render(self, **kwargs):
        map_obj = self._parent
        base_maps = {}
        overlay_maps = {}

        # Find all layers in the map's script children
        layers = [child for child in map_obj._figure.script._children.values() if isinstance(child, Layer)]
        
        for layer in layers:
            if layer.layer_name and layer.show:
                if layer.overlay:
                    overlay_maps[layer.layer_name] = layer.get_name()
                else:
                    base_maps[layer.layer_name] = layer.get_name()

        # The JS needs variable names, not JSON strings for the values
        def format_js_object(d):
            items = [f'"{key}": {value}' for key, value in d.items()]
            return "{" + ", ".join(items) + "}"

        options = _parse_options(**self.kwargs)
        return Template(self._template).render(
            base_maps=format_js_object(base_maps),
            overlay_maps=format_js_object(overlay_maps),
            options=options,
            map=map_obj.get_name()
        )