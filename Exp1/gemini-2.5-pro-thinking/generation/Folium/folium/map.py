# folium/map.py
import json
from folium.elements import Element, Figure, Template
from folium.utilities import _validate_location, _parse_size, _parse_options

# Default resources
JQUERY_JS = '<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>'
LEAFLET_CSS = '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.css"/>'
LEAFLET_JS = '<script src="https://cdn.jsdelivr.net/npm/leaflet@1.9.4/dist/leaflet.js"></script>'

class Layer(Element):
    """Base class for all map layers."""
    def __init__(self, name=None, show=True, overlay=True):
        super().__init__()
        self.layer_name = name
        self.show = show
        self.overlay = overlay
    
    def get_name(self):
        """Returns a unique JS variable name for the layer."""
        return f"{self._name.lower()}_{self._id}"

class FeatureGroup(Layer):
    """A group of layers that can be controlled together."""
    _template = """
    var {variable} = L.featureGroup().addTo({map});
    """
    def __init__(self, name=None, show=True, overlay=True):
        super().__init__(name=name, show=show, overlay=overlay)
        self._name = "FeatureGroup"

    def render(self, **kwargs):
        script = Template(self._template).render(
            variable=self.get_name(),
            map=self._parent.get_name()
        )
        for child in self._children.values():
            child._parent = self
            script += child.render(**kwargs)
        return script

class Map(Layer):
    """The main Map object."""
    def __init__(self, location=None, zoom_start=10, tiles="OpenStreetMap", width="100%", height="100%", **kwargs):
        super().__init__()
        self._name = "Map"
        self._figure = Figure(width=width, height=height)

        if location:
            self.location = _validate_location(location)
        else:
            self.location = [0, 0]
        self.zoom_start = zoom_start
        self.kwargs = kwargs

        # Add dependencies to the figure header
        self._figure.header.add_child(Element(), name='jquery')._template = JQUERY_JS
        self._figure.header.add_child(Element(), name='leaflet_css')._template = LEAFLET_CSS
        self._figure.header.add_child(Element(), name='leaflet_js')._template = LEAFLET_JS

        # Add the map div to the figure html
        self.div = Element()
        self.div._template = f'<div id="{self.get_name()}" style="width: {_parse_size(width)}; height: {_parse_size(height)}; position: relative; outline: none;"></div>'
        self._figure.html.add_child(self.div)

        # Add the map initialization script
        self.script = Element()
        options = _parse_options(
            zoom=self.zoom_start,
            center=self.location,
            **self.kwargs
        )
        self.script._template = f"""
        var {self.get_name()} = L.map('{self.get_name()}', {options});
        """
        self._figure.script.add_child(self.script)

        # Add the default tile layer
        if tiles:
            from folium.raster_layers import TileLayer
            TileLayer(tiles, name=tiles, overlay=False).add_to(self)

    def get_name(self):
        return f"map_{self._id}"

    def add_child(self, child, name=None, index=None):
        """Add a child to the map's script part."""
        self._figure.script.add_child(child, name=name, index=index)
        child._parent = self
        return self

    def get_root(self):
        """Return the Figure object."""
        return self._figure

    def render(self, **kwargs):
        """Render the complete HTML page."""
        # Ensure LayerControl is rendered last
        layer_control = None
        for name, child in list(self._figure.script._children.items()):
            if "LayerControl" in child._name:
                layer_control = self._figure.script._children.pop(name)
        
        if layer_control:
            self._figure.script.add_child(layer_control)

        return self._figure.render(**kwargs)