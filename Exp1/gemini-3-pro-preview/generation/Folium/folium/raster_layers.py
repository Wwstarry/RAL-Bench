from folium.elements import Element

class TileLayer(Element):
    def __init__(self, tiles="OpenStreetMap", attr=None, name=None, overlay=False, control=True):
        super().__init__()
        self.tiles = tiles
        self.attr = attr
        self.name = name if name else "TileLayer"
        self.overlay = overlay
        self.control = control
        
        self._provider_url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        self._provider_attr = 'Data by &copy; <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.'

        if self.tiles == "OpenStreetMap":
            self.tiles = self._provider_url
            if self.attr is None:
                self.attr = self._provider_attr

    def to_javascript(self, parent_name):
        return f"""
            var {self.get_name()} = L.tileLayer(
                "{self.tiles}",
                {{
                    "attribution": '{self.attr if self.attr else ""}',
                    "detectRetina": false,
                    "maxNativeZoom": 18,
                    "maxZoom": 18,
                    "minZoom": 0,
                    "noWrap": false,
                    "opacity": 1,
                    "subdomains": "abc",
                    "tms": false
                }}
            ).addTo({parent_name});
        """