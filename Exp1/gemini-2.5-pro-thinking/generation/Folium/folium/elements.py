# folium/elements.py
import uuid
from collections import OrderedDict

class Element:
    """Base class for all Folium objects."""
    _template = ""

    def __init__(self):
        self._name = self.__class__.__name__
        self._id = uuid.uuid4().hex
        self._children = OrderedDict()
        self._parent = None

    def add_child(self, child, name=None, index=None):
        """Add a child to the element."""
        if name is None:
            name = child._name + "_" + child._id
        if index is None:
            self._children[name] = child
        else:
            items = list(self._children.items())
            items.insert(index, (name, child))
            self._children = OrderedDict(items)
        child._parent = self
        return self

    def add_to(self, parent, name=None, index=None):
        """Add this element to a parent element."""
        parent.add_child(self, name=name, index=index)
        return self

    def get_root(self):
        """Get the top-level parent of this element."""
        if self._parent is None:
            return self
        return self._parent.get_root()

    def render(self, **kwargs):
        """Render the element and its children."""
        # This will be overridden by subclasses.
        for child in self._children.values():
            child.render(**kwargs)

    def _repr_html_(self):
        """Render for Jupyter Notebooks."""
        return self.get_root().render()

class Figure(Element):
    """The top-level container for a map."""
    _template = """
<!DOCTYPE html>
<html>
<head>
    <meta http-equiv="content-type" content="text/html; charset=UTF-8" />
    <title>Folium Map</title>
    <script>L_NO_TOUCH = false; L_DISABLE_3D = false;</script>
    {header}
</head>
<body>
    {html}
    <script>
        {script}
    </script>
</body>
</html>
"""
    def __init__(self, width="100%", height="100%"):
        super().__init__()
        self.header = Element()
        self.html = Element()
        self.script = Element()
        self.width = width
        self.height = height
        self._children = OrderedDict([
            ('header', self.header),
            ('html', self.html),
            ('script', self.script)
        ])

    def render(self, **kwargs):
        """Render the full HTML page."""
        header = "".join(child.render(**kwargs) for child in self.header._children.values())
        html = "".join(child.render(**kwargs) for child in self.html._children.values())
        script = "".join(child.render(**kwargs) for child in self.script._children.values())
        return self._template.format(header=header, html=html, script=script)

class Template(Element):
    """A simple template renderer using str.format."""
    def __init__(self, template):
        super().__init__()
        self._template = template

    def render(self, **kwargs):
        return self._template.format(**kwargs)