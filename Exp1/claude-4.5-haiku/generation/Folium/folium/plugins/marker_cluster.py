"""
MarkerCluster plugin for grouping nearby markers.
"""

import json
import uuid
from folium.map import Element


class MarkerCluster(Element):
    """
    Add marker clustering to the map.
    
    Parameters
    ----------
    options : dict, optional
        Clustering options (e.g., maxClusterRadius, disableClusteringAtZoom)
    """

    def __init__(self, options: dict = None):
        super().__init__()
        self.options = options or {}
        self.markers = []

    def add_child(self, child):
        """Add a marker to the cluster."""
        if hasattr(child, 'location'):
            self.markers.append(child)
        return super().add_child(child)

    def _render_js(self, map_id: str) -> str:
        """Render JavaScript to add marker cluster to map."""
        cluster_id = f"cluster_{self._id}"
        
        options_str = json.dumps(self.options) if self.options else "{}"
        
        js_lines = [
            '        <script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.1/leaflet.markercluster.min.js"></script>',
            '        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.1/MarkerCluster.css" />',
            '        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.1/MarkerCluster.Default.css" />',
            f'        var {cluster_id} = L.markerClusterGroup({options_str});',
        ]
        
        # Add markers to cluster
        for marker in self.markers:
            marker_id = f"marker_{marker._id}"
            js_lines.append(
                f'        var {marker_id} = L.marker([{marker.location[0]}, {marker.location[1]}]);'
            )
            js_lines.append(f'        {cluster_id}.addLayer({marker_id});')
        
        js_lines.append(f'        map.addLayer({cluster_id});')
        
        return '\n'.join(js_lines)