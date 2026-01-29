import json
from folium.elements import Element

class GeoJson(Element):
    def __init__(self, data, name=None):
        super().__init__()
        self.data = data
        self._name = name

    def to_javascript(self, parent_name):
        # We dump the data to a JS object
        data_str = json.dumps(self.data)
        return f"""
            var {self.get_name()} = L.geoJson(
                {data_str},
                {{}}
            ).addTo({parent_name});
        """