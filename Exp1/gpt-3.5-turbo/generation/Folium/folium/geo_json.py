import json

class GeoJson:
    def __init__(self, data, name=None):
        # data can be dict or JSON string
        if isinstance(data, str):
            self.data = json.loads(data)
        else:
            self.data = data
        self.name = name or f'geojson_{id(self)}'
        self._name = self.name

    def get_name(self):
        return self._name

    def _render_js(self):
        # Dump GeoJSON data as JSON string
        geojson_str = json.dumps(self.data)
        js = (f'var {self._name} = L.geoJSON({geojson_str});'
              f'{self._name}.addTo(map);')
        return js