from ..base import Element

class MarkerCluster(Element):
    """Marker cluster plugin for Leaflet."""
    def _render_js(self, map_name):
        """Generate JavaScript for marker cluster."""
        cluster_name = self.get_name()
        js = [
            f'var {cluster_name} = L.markerClusterGroup();',
            f'{map_name}.addLayer({cluster_name});'
        ]
        # Add child markers to cluster
        for child in self._children.values():
            js.append(child._render_js(cluster_name).replace(f'.addTo({map_name})', f'.addTo({cluster_name})'))
        return ''.join(js)

    def render(self):
        return ''