"""
Marker Cluster plugin
"""

from ..features import BaseFeature

class MarkerCluster(BaseFeature):
    def __init__(self):
        super().__init__()
        self._markers = []
        self._is_marker_cluster_plugin = True

    def add_child(self, marker):
        self._markers.append(marker)

    def add_to(self, parent):
        parent.add_child(self)

    def render(self):
        """
        Renders a marker cluster group with any child markers within it.
        """
        cluster_group_var = "marker_cluster_group"
        script_parts = [f"var {cluster_group_var} = L.markerClusterGroup();\n"]

        for marker in self._markers:
            # Marker is a BaseFeature. We can get a minimal script from it.
            marker_script, _ = marker.render()
            # Adjust it to add to cluster group instead of "map"
            marker_script = marker_script.replace("addTo(map)", f"addTo({cluster_group_var})")
            script_parts.append(marker_script)

        script_parts.append(f"{cluster_group_var}.addTo(map);\n")
        return ("".join(script_parts), "")