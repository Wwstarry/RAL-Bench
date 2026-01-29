class LayerControl:
    def __init__(self):
        self._name = 'layer_control'

    def get_name(self):
        return self._name

    def _render_js(self):
        return 'L.control.layers().addTo(map);'