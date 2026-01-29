import json

from .map import MacroElement

class Marker(MacroElement):
    def __init__(self, location, popup=None, tooltip=None, **kwargs):
        super().__init__()
        self.location = location
        self.popup = popup
        self.tooltip = tooltip
        self.options = kwargs

    def render(self, map_var='map', **kwargs):
        js = f'L.marker({json.dumps(self.location)})'
        opts = []
        if self.popup:
            opts.append(f'.bindPopup({json.dumps(self.popup)})')
        if self.tooltip:
            opts.append(f'.bindTooltip({json.dumps(self.tooltip)})')
        js += ''.join(opts)
        js += f'.addTo({map_var});'
        return js

class CircleMarker(MacroElement):
    def __init__(self, location, radius=10, color='#3388ff', fill=True, fill_color=None, popup=None, tooltip=None, **kwargs):
        super().__init__()
        self.location = location
        self.radius = radius
        self.color = color
        self.fill = fill
        self.fill_color = fill_color or color
        self.popup = popup
        self.tooltip = tooltip
        self.options = kwargs

    def render(self, map_var='map', **kwargs):
        options = {
            'radius': self.radius,
            'color': self.color,
            'fill': self.fill,
            'fillColor': self.fill_color
        }
        options.update(self.options)
        js = f'L.circleMarker({json.dumps(self.location)}, {json.dumps(options)})'
        opts = []
        if self.popup:
            opts.append(f'.bindPopup({json.dumps(self.popup)})')
        if self.tooltip:
            opts.append(f'.bindTooltip({json.dumps(self.tooltip)})')
        js += ''.join(opts)
        js += f'.addTo({map_var});'
        return js