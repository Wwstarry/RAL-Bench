import json

class Map:
    def __init__(self, location=None, zoom_start=10, tiles="OpenStreetMap"):
        self.location = location or [0, 0]
        self.zoom_start = zoom_start
        self.tiles = tiles
        self.layers = []
        self.controls = []

    def add_child(self, child):
        if isinstance(child, LayerControl):
            self.controls.append(child)
        else:
            self.layers.append(child)

    def get_root(self):
        return self

    def render(self):
        html = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Map</title>",
            '<link rel="stylesheet" href="https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"/>',
            '<script src="https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"></script>',
            "</head>",
            "<body>",
            '<div id="map" style="width: 100%; height: 100%;"></div>',
            "<script>",
            "var map = L.map('map').setView({}, {});".format(self.location, self.zoom_start),
        ]

        if self.tiles:
            html.append(f"L.tileLayer('{self.tiles}').addTo(map);")

        for layer in self.layers:
            html.append(layer.render())

        for control in self.controls:
            html.append(control.render())

        html.append("</script>")
        html.append("</body>")
        html.append("</html>")
        return "\n".join(html)