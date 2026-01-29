from .base import Element

class LayerControl(Element):
    """Layer control for toggling overlays."""
    def _render_js(self, map_name):
        """Generate JavaScript for layer control."""
        return f'L.control.layers({{}}, {{}}, {{collapsed: false}}).addTo({map_name});'

    def render(self):
        return ''