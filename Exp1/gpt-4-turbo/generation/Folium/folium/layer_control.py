from .map import MacroElement

class LayerControl(MacroElement):
    def __init__(self, position='topright', **kwargs):
        super().__init__()
        self.position = position
        self.options = kwargs

    def render(self, map_var='map', **kwargs):
        js = f'L.control.layers(null, null, {{position: "{self.position}"}}).addTo({map_var});'
        return js