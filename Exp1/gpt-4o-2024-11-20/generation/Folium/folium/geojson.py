class GeoJson:
    def __init__(self, data):
        self.data = data

    def render(self):
        return f"L.geoJSON({json.dumps(self.data)}).addTo(map);"