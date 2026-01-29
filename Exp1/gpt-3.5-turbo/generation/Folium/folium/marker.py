class Marker:
    def __init__(self, location, popup=None, tooltip=None, icon=None):
        self.location = location
        self.popup = popup
        self.tooltip = tooltip
        self.icon = icon
        self._name = f'marker_{id(self)}'

    def get_name(self):
        return self._name

    def _render_js(self):
        lat, lng = self.location
        js = f'var {self._name} = L.marker([{lat}, {lng}]);'
        if self.popup is not None:
            js += f'{self._name}.bindPopup("{self._escape(self.popup)}");'
        if self.tooltip is not None:
            js += f'{self._name}.bindTooltip("{self._escape(self.tooltip)}");'
        js += f'{self._name}.addTo(map);'
        return js

    def _escape(self, text):
        # Simple escape for quotes and newlines
        return str(text).replace('"', '\\"').replace('\n', '\\n')

class CircleMarker:
    def __init__(self, location, radius=10, color='#3388ff', fill=True, fill_color=None, fill_opacity=0.2, popup=None, tooltip=None):
        self.location = location
        self.radius = radius
        self.color = color
        self.fill = fill
        self.fill_color = fill_color or color
        self.fill_opacity = fill_opacity
        self.popup = popup
        self.tooltip = tooltip
        self._name = f'circle_marker_{id(self)}'

    def get_name(self):
        return self._name

    def _render_js(self):
        lat, lng = self.location
        js = (f'var {self._name} = L.circleMarker([{lat}, {lng}], '
              f'{{radius: {self.radius}, color: "{self.color}", fill: {str(self.fill).lower()}, '
              f'fillColor: "{self.fill_color}", fillOpacity: {self.fill_opacity}}});')
        if self.popup is not None:
            js += f'{self._name}.bindPopup("{self._escape(self.popup)}");'
        if self.tooltip is not None:
            js += f'{self._name}.bindTooltip("{self._escape(self.tooltip)}");'
        js += f'{self._name}.addTo(map);'
        return js

    def _escape(self, text):
        return str(text).replace('"', '\\"').replace('\n', '\\n')