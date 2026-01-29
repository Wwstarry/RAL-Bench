from .map import MacroElement
import json

_tile_urls = {
    'OpenStreetMap': 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    'Stamen Terrain': 'https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.png',
    'Stamen Toner': 'https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png',
    'CartoDB positron': 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
}

_tile_attributions = {
    'OpenStreetMap': '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    'Stamen Terrain': 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, CC BY 3.0 &mdash; Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    'Stamen Toner': 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, CC BY 3.0 &mdash; Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    'CartoDB positron': '&copy; <a href="https://carto.com/attributions">CARTO</a>',
}

class TileLayer(MacroElement):
    def __init__(self, tiles='OpenStreetMap', name=None, attr=None, **kwargs):
        super().__init__()
        self.tiles = tiles
        self.name = name or tiles
        self.attr = attr or _tile_attributions.get(tiles, '')
        self.options = kwargs

    def render(self, map_var='map', **kwargs):
        url = _tile_urls.get(self.tiles, self.tiles)
        js = f'L.tileLayer({json.dumps(url)}, {{attribution: {json.dumps(self.attr)}}})'
        js += f'.addTo({map_var});'
        return js