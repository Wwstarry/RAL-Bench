class TileLayer:
    def __init__(self, tiles='OpenStreetMap', attr=None, name=None, overlay=True, control=True):
        self.tiles = tiles
        self.attr = attr
        self.name = name or tiles
        self.overlay = overlay
        self.control = control
        self._name = f'tile_layer_{id(self)}'

    def get_name(self):
        return self._name

    def _render_js(self):
        # Provide tile URL and attribution for known providers
        tile_url, attribution = self._get_tile_url_and_attr(self.tiles, self.attr)
        # Compose JS to add tile layer to map
        js = f'var {self._name} = L.tileLayer("{tile_url}", {{attribution: "{attribution}", overlay: {str(self.overlay).lower()}, name: "{self.name}"}}).addTo(map);'
        return js

    def _get_tile_url_and_attr(self, tiles, attr):
        # Support only OpenStreetMap for now, else assume tiles is a URL template
        if tiles == 'OpenStreetMap':
            url = "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            attribution = attr or '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            return url, attribution
        else:
            # Assume tiles is URL template string
            return tiles, attr or ''