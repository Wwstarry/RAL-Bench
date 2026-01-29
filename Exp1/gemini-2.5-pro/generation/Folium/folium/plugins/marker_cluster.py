from folium.map import Layer, MacroElement
from folium.features import Marker
from folium.utilities import get_name

MARKER_CLUSTER_JS = "https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.1/leaflet.markercluster.js"
MARKER_CLUSTER_CSS = "https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.1/MarkerCluster.css"
MARKER_CLUSTER_DEFAULT_CSS = "https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.1/MarkerCluster.Default.css"


class MarkerCluster(Layer, MacroElement):
    """A layer for clustering markers."""

    _template = """
    var {variable} = L.markerClusterGroup();
    {map_variable}.addLayer({variable});
    """

    def __init__(self, locations=None, name=None, overlay=True, control=True):
        super().__init__(name=name, overlay=overlay, control=control)
        self._name = "marker_cluster_" + self._id
        self._children = [
            ("marker_cluster_js", MARKER_CLUSTER_JS),
            ("marker_cluster_css", MARKER_CLUSTER_CSS),
            ("marker_cluster_default_css", MARKER_CLUSTER_DEFAULT_CSS),
        ]
        if locations:
            for loc in locations:
                self.add_child(Marker(loc))

    def render(self, **kwargs):
        map_variable = self.get_root().get_name()
        cluster_variable = self.get_name()

        # Render the cluster group initialization
        html = self._template.format(
            variable=cluster_variable,
            map_variable=map_variable
        )

        # Render each child marker and add it to the cluster group
        for child in self.children.values():
            if isinstance(child, Marker):
                # Temporarily change the parent to render correctly
                original_parent = child.parent
                child.parent = self
                
                # Render the marker but add it to the cluster, not the map
                marker_html = child.render().replace(
                    f".addTo({map_variable})",
                    f".addTo({cluster_variable})"
                )
                html += marker_html
                
                # Restore original parent
                child.parent = original_parent
        return html