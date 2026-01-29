class TileLayer:
    def __init__(self, tiles="OpenStreetMap"):
        self.tiles = tiles

    def render(self):
        return f"L.tileLayer('{self.tiles}').addTo(map);"