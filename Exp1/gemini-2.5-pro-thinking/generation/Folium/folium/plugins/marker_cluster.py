# folium/plugins/marker_cluster.py
from folium.map import FeatureGroup
from folium.elements import Element, Template
from folium.utilities import _parse_options

MARKER_CLUSTER_CSS = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.1/MarkerCluster.css"/>'
MARKER_CLUSTER_DEFAULT_CSS = '<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.1/MarkerCluster.Default.css"/>'
MARKER_CLUSTER_JS = '<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.1/leaflet.markercluster.js"></script>'

class MarkerCluster(FeatureGroup):
    """A MarkerCluster layer."""
    _template = """
    var {variable} = L.markerClusterGroup({options});
    {map}.addLayer({variable});
    """
    def __init__(self, locations=None, popups=None, name=None, overlay=True, show=True, **kwargs):
        super().__init__(name=name or "MarkerCluster", overlay=overlay, show=show)
        self._name = "MarkerCluster"
        self.kwargs = kwargs

        if locations:
            from folium.features import Marker
            for i, loc in enumerate(locations):
                popup = popups[i] if popups and i < len(popups) else None
                Marker(location=loc, popup=popup).add_to(self)

    def add_to(self, parent, name=None, index=None):
        """Adds the plugin to the map."""
        super().add_to(parent, name, index)
        # Add dependencies to the map's header
        figure = self.get_root()
        figure.header.add_child(Element(), name='marker_cluster_css')._template = MARKER_CLUSTER_CSS
        figure.header.add_child(Element(), name='marker_cluster_default_css')._template = MARKER_CLUSTER_DEFAULT_CSS
        figure.header.add_child(Element(), name='marker_cluster_js')._template = MARKER_CLUSTER_JS
        return self

    def render(self, **kwargs):
        options = _parse_options(**self.kwargs)
        script = Template(self._template).render(
            variable=self.get_name(),
            options=options,
            map=self._parent.get_name()
        )
        # Render children to be added to this cluster, not the map
        for child in self._children.values():
            child._parent = self
            script += child.render(**kwargs)
        return script