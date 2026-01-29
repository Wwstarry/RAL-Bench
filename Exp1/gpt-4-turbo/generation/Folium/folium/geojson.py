import json

from .map import MacroElement

class GeoJson(MacroElement):
    def __init__(self, data, name=None, **kwargs):
        super().__init__()
        self.data = data
        self.name = name
        self.options = kwargs

    def render(self, map_var='map', **kwargs):
        # Accept dict or string
        if isinstance(self.data, dict):
            geojson_str = json.dumps(self.data)
        else:
            geojson_str = self.data
        opts = ''
        if self.name:
            opts = f', {{name: {json.dumps(self.name)}}}'
        js = f'L.geoJSON({geojson_str}{opts}).addTo({map_var});'
        return js