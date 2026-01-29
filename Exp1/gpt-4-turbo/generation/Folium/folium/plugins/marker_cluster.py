import json
from ..map import MacroElement

class MarkerCluster(MacroElement):
    def __init__(self, markers=None, name=None, **kwargs):
        super().__init__()
        self.markers = markers or []
        self.name = name
        self.options = kwargs

    def add_child(self, marker):
        self.markers.append(marker)
        marker._parent = self
        return self

    def render(self, map_var='map', **kwargs):
        # Add plugin script
        js = []
        js.append('var marker_cluster = L.markerClusterGroup();')
        for marker in self.markers:
            # Render marker as JS, but replace .addTo(map) with .addTo(marker_cluster)
            marker_js = marker.render(map_var='marker_cluster')
            js.append(marker_js)
        js.append(f'marker_cluster.addTo({map_var});')
        return '\n'.join(js)

    def _get_plugin_scripts(self):
        # Returns <script src=...> for leaflet.markercluster
        return [
            '<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"/>',
            '<link rel="stylesheet" href="https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"/>',
            '<script src="https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"></script>'
        ]