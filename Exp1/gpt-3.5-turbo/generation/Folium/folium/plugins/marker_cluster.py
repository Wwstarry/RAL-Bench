class MarkerCluster:
    def __init__(self, name=None):
        self._name = name or f'marker_cluster_{id(self)}'
        self._markers = []

    def get_name(self):
        return self._name

    def add_child(self, marker):
        # Accept Marker or CircleMarker instances
        self._markers.append(marker)
        return self

    def _render_js(self):
        js = []
        js.append(f'var {self._name} = L.markerClusterGroup();')
        for marker in self._markers:
            # Render marker JS but do not add to map directly, instead add to cluster
            lat, lng = marker.location
            # Compose marker options for CircleMarker or Marker
            if hasattr(marker, 'radius'):
                # CircleMarker
                options = (f'{{radius: {marker.radius}, color: "{marker.color}", fill: {str(marker.fill).lower()}, '
                           f'fillColor: "{marker.fill_color}", fillOpacity: {marker.fill_opacity}}}')
                js.append(f'var m_{id(marker)} = L.circleMarker([{lat}, {lng}], {options});')
                if marker.popup is not None:
                    js.append(f'm_{id(marker)}.bindPopup("{self._escape(marker.popup)}");')
                if marker.tooltip is not None:
                    js.append(f'm_{id(marker)}.bindTooltip("{self._escape(marker.tooltip)}");')
                js.append(f'{self._name}.addLayer(m_{id(marker)});')
            else:
                # Marker
                js.append(f'var m_{id(marker)} = L.marker([{lat}, {lng}]);')
                if marker.popup is not None:
                    js.append(f'm_{id(marker)}.bindPopup("{self._escape(marker.popup)}");')
                if marker.tooltip is not None:
                    js.append(f'm_{id(marker)}.bindTooltip("{self._escape(marker.tooltip)}");')
                js.append(f'{self._name}.addLayer(m_{id(marker)});')
        js.append(f'{self._name}.addTo(map);')
        return '\n'.join(js)

    def _escape(self, text):
        return str(text).replace('"', '\\"').replace('\n', '\\n')