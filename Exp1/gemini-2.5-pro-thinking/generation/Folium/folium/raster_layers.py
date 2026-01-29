# folium/raster_layers.py
from folium.map import Layer
from folium.elements import Template
from folium.utilities import _parse_options

# Pre-defined tile providers
TILE_PROVIDERS = {
    "OpenStreetMap": {
        "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    },
    "Stamen Terrain": {
        "url": "https://stamen-tiles-{s}.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png",
        "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
    },
    "Stamen Toner": {
        "url": "https://stamen-tiles-{s}.a.ssl.fastly.net/toner/{z}/{x}/{y}.png",
        "attr": 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, under <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a>. Data by <a href="http://openstreetmap.org">OpenStreetMap</a>, under <a href="http://www.openstreetmap.org/copyright">ODbL</a>.',
    }
}

class TileLayer(Layer):
    """A tile layer for the map."""
    _template = """
    var {variable} = L.tileLayer(
        '{url}',
        {options}
    ).addTo({map});
    """
    def __init__(self, tiles="OpenStreetMap", attr=None, name=None, overlay=False, show=True, **kwargs):
        super().__init__(name=name, overlay=overlay, show=show)
        self._name = "TileLayer"
        
        if tiles in TILE_PROVIDERS:
            self.tiles = TILE_PROVIDERS[tiles]["url"]
            self.attr = attr or TILE_PROVIDERS[tiles]["attr"]
        else:
            self.tiles = tiles
            self.attr = attr

        self.kwargs = kwargs
        self.kwargs['attribution'] = self.attr

    def render(self, **kwargs):
        options = _parse_options(**self.kwargs)
        return Template(self._template).render(
            variable=self.get_name(),
            url=self.tiles,
            options=options,
            map=self._parent.get_name()
        )