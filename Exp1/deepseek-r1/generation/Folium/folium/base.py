import uuid

class Element:
    """Base class for all folium elements."""
    def __init__(self):
        self._id = uuid.uuid4().hex
        self._children = {}
        self._parent = None

    def get_name(self):
        return f"{self.__class__.__name__.lower()}_{self._id}"

    def add_to(self, parent):
        """Add element to a parent container."""
        parent._children[self.get_name()] = self
        self._parent = parent
        return self

    def render(self):
        """Render HTML/JS representation of the element."""
        raise NotImplementedError