import json
import uuid
from collections import OrderedDict

from . import templates
from .utilities import get_name, json_dump


class Element:
    """Basic building block for all Folium objects.

    Represents an object that can be rendered into an HTML/JS/CSS representation.
    """

    _template = ""

    def __init__(self):
        self._id = uuid.uuid4().hex
        self.children = OrderedDict()
        self.parent = None
        self._name = self.__class__.__name__.lower() + "_" + self._id

    def get_name(self):
        """Returns the unique variable name of the element."""
        return get_name(self)

    def add_child(self, child, name=None, index=None):
        """Add a child element to this element."""
        if name:
            child._name = name
        self.children[child._id] = child
        child.parent = self

    def get_root(self):
        """Finds the root of the element tree."""
        if self.parent is None:
            return self
        else:
            return self.parent.get_root()

    def render(self, **kwargs):
        """Renders the object to HTML/JS/CSS."""
        if self._template:
            return self._template.render(**self.get_root()._get_template_variables())
        return ""

    def _repr_html_(self):
        """Renders the object in a Jupyter notebook."""
        return self.get_root().render()


class MacroElement(Element):
    """An element that adds something to the <head> of the document."""

    def __init__(self):
        super().__init__()
        self._children = []

    def add_to(self, parent):
        parent.add_child(self)


class Layer(Element):
    """A class for objects that can be added to a Map."""

    def __init__(self, name=None, overlay=True, control=True, show=True):
        super().__init__()
        self.layer_name = name if name is not None else self.get_name()
        self.overlay = overlay
        self.control = control
        self.show = show

    def add_to(self, parent):
        """Adds the layer to a parent object (e.g., a Map)."""
        parent.add_child(self)
        return self


class Map(Element):
    """The main Map object."""

    _template = templates.HTML_TEMPLATE

    def __init__(self, location=None, zoom_start=10, tiles="OpenStreetMap", **kwargs):
        super().__init__()
        self._name = "map"
        self.location = location if location is not None else [0, 0]
        self.zoom_start = zoom_start
        self.js = []
        self.css = []

        # Add default Leaflet JS/CSS
        self.js.append(("leaflet", templates.LEAFLET_JS))
        self.css.append(("leaflet", templates.LEAFLET_CSS))

        if tiles:
            self.add_child(TileLayer(tiles))

    def _get_template_variables(self):
        """Get the variables for rendering the map template."""
        header = ""
        for _, url in sorted(list(set(self.css))):
            header += templates.CSS_LINK.format(url=url)
        for _, url in sorted(list(set(self.js))):
            header += templates.JS_LINK.format(url=url)

        script = ""
        for child in self.children.values():
            try:
                script += child.render()
            except Exception as e:
                # Allows rendering to continue if a child fails.
                pass

        return {
            "header": header,
            "map_id": self._id,
            "map_variable": self.get_name(),
            "location": json.dumps(self.location),
            "zoom_start": self.zoom_start,
            "script": script,
        }

    def render(self):
        """Renders the map to HTML."""
        # Collect JS/CSS from all children
        for child in self.children.values():
            if isinstance(child, MacroElement):
                for url in child._children:
                    if url[1].endswith(".js"):
                        self.js.append((url[0], url[1]))
                    elif url[1].endswith(".css"):
                        self.css.append((url[0], url[1]))

        return self._template.format(**self._get_template_variables())