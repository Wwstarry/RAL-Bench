class MarkerCluster:
    def __init__(self):
        self.markers = []

    def add_child(self, marker):
        self.markers.append(marker)

    def render(self):
        cluster_js = [
            '<script src="https://unpkg.com/leaflet.markercluster@1.4.1/dist/leaflet.markercluster.js"></script>',
            '<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.css"/>',
            '<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.4.1/dist/MarkerCluster.Default.css"/>',
            "var markers = L.markerClusterGroup();",
        ]
        for marker in self.markers:
            cluster_js.append(marker.render().replace(".addTo(map);", ".addTo(markers);"))
        cluster_js.append("map.addLayer(markers);")
        return "\n".join(cluster_js)