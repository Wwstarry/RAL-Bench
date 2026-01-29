import uuid
from collections import OrderedDict

class Element:
    """Base class for all Folium elements."""
    def __init__(self):
        self._id = "e" + uuid.uuid4().hex
        self._children = OrderedDict()
        self._parent = None

    def add_child(self, child, name=None):
        if name is None:
            name = child.get_name()
        self._children[name] = child
        child._parent = self
        return self

    def add_to(self, parent, name=None):
        parent.add_child(self, name=name)
        return self

    def get_name(self):
        return self._id

    def get_root(self):
        if self._parent:
            return self._parent.get_root()
        return self

    def render(self, **kwargs):
        """Renders the element. usually called on the root Figure."""
        pass

    def to_javascript(self, parent_name):
        """Returns the JS code to initialize this element and add it to parent."""
        return ""

    def get_css_links(self):
        """Return a list of CSS URLs required by this element."""
        return []

    def get_js_links(self):
        """Return a list of JS URLs required by this element."""
        return []

class Figure(Element):
    """The root element that generates the HTML file structure."""
    def __init__(self):
        super().__init__()
        self.header_content = []
        
    def render(self, **kwargs):
        # Collect all dependencies
        css_links = []
        js_links = []
        
        def collect_deps(elem):
            css_links.extend(elem.get_css_links())
            js_links.extend(elem.get_js_links())
            for child in elem._children.values():
                collect_deps(child)
        
        collect_deps(self)
        
        # Deduplicate preserving order
        css_links = list(OrderedDict.fromkeys(css_links))
        js_links = list(OrderedDict.fromkeys(js_links))
        
        # Generate HTML
        html = []
        html.append("<!DOCTYPE html>")
        html.append("<html>")
        html.append("<head>")
        html.append('<meta http-equiv="content-type" content="text/html; charset=UTF-8" />')
        
        for css in css_links:
            html.append(f'<link rel="stylesheet" href="{css}"/>')
        for js in js_links:
            html.append(f'<script src="{js}"></script>')
            
        html.append("<style>html, body {width: 100%;height: 100%;margin: 0;padding: 0;}</style>")
        html.append("<style>#map {position:absolute;top:0;bottom:0;right:0;left:0;}</style>")
        html.append("</head>")
        html.append("<body>")
        
        # Render HTML of children (e.g. the map div)
        # We assume the Figure has one main child (the Map) or multiple
        # But usually Map creates the div.
        
        # We need to traverse to find HTML content
        def collect_html(elem):
            content = ""
            if hasattr(elem, 'to_html'):
                content += elem.to_html()
            for child in elem._children.values():
                content += collect_html(child)
            return content

        html.append(collect_html(self))
        
        html.append("<script>")
        
        # Render JS
        # We traverse the tree. 
        # The root (Figure) doesn't have a JS variable usually, but its children do.
        
        def collect_js(elem, parent_var):
            js = ""
            if hasattr(elem, 'to_javascript'):
                # If it's the Map element, it doesn't need a parent_var to add to (it attaches to div)
                # But others do.
                js += elem.to_javascript(parent_var)
            
            # Recurse
            # The current element's variable name becomes the parent for its children
            current_var = elem.get_name()
            # Some elements might not define a variable (like Figure), so we pass down the parent
            if not hasattr(elem, 'to_javascript'):
                current_var = parent_var
            
            for child in elem._children.values():
                js += collect_js(child, current_var)
            return js

        html.append(collect_js(self, None))
        
        html.append("</script>")
        html.append("</body>")
        html.append("</html>")
        
        return "\n".join(html)

class MacroElement(Element):
    """Base class for elements that don't have a physical presence on the map but affect it."""
    pass