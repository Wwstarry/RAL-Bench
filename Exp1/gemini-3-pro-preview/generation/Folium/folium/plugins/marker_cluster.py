from folium.elements import Element

class MarkerCluster(Element):
    def __init__(self, name=None, overlay=True, control=True, show=True):
        super().__init__()
        self._name = name if name else "MarkerCluster"
        self.overlay = overlay
        self.control = control
        self.show = show

    def get_css_links(self):
        return [
            "https://cdnjs.cloudflare.com/ajax/libs/Leaflet.markercluster/1.1.0/MarkerCluster.css",
            "https://cdnjs.cloudflare.com/ajax/libs/Leaflet.markercluster/1.1.0/MarkerCluster.Default.css"
        ]

    def get_js_links(self):
        return [
            "https://cdnjs.cloudflare.com/ajax/libs/Leaflet.markercluster/1.1.0/leaflet.markercluster.js"
        ]

    def to_javascript(self, parent_name):
        return f"""
            var {self.get_name()} = L.markerClusterGroup(
                {{}}
            );
            {parent_name}.addLayer({self.get_name()});
        """