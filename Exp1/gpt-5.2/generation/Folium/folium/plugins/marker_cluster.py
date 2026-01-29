from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from ..elements import MacroElement
from ..util import get_name, tojson

LatLng = Union[Tuple[float, float], List[float]]


_MARKERCLUSTER_JS = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"
_MARKERCLUSTER_CSS = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"
_MARKERCLUSTER_CSS_DEFAULT = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"


class MarkerCluster(MacroElement):
    """
    Minimal MarkerCluster plugin.

    To reduce output size for many markers, this class supports an efficient bulk API:
      - add_child(Marker(...)) will still work (renders per marker)
      - add_locations([(lat, lon), ...], popup=None/str/callable) to store coords and emit a compact JS loop
    """
    def __init__(self, name: Optional[str] = None, overlay: bool = True, control: bool = True, show: bool = True, **kwargs: Any):
        super().__init__(name="marker_cluster")
        self.layer_name = name or "MarkerCluster"
        self.overlay = overlay
        self.control = control
        self.show = show
        self.kwargs = dict(kwargs)
        self._id = get_name("marker_cluster")
        self._locations: List[List[float]] = []
        self._popup: Optional[Union[str, Sequence[Optional[str]]]] = None

    def get_name(self) -> str:
        return self._id

    def add_locations(self, locations: Sequence[LatLng], popup: Optional[Union[str, Sequence[Optional[str]]]] = None) -> "MarkerCluster":
        for loc in locations:
            self._locations.append([float(loc[0]), float(loc[1])])
        if popup is not None:
            self._popup = popup
        return self

    def _map_var(self) -> str:
        obj = self
        while obj._parent is not None:
            if getattr(obj._parent, "_name", None) == "map":
                return obj._parent.get_name()  # type: ignore[attr-defined]
            obj = obj._parent
        return "map"

    def render(self, **kwargs: Any) -> str:
        fig = self.get_root()
        fig.add_header(f'<link rel="stylesheet" href="{_MARKERCLUSTER_CSS}"/>')
        fig.add_header(f'<link rel="stylesheet" href="{_MARKERCLUSTER_CSS_DEFAULT}"/>')
        fig.add_header(f'<script src="{_MARKERCLUSTER_JS}"></script>')

        mvar = self._map_var()
        layer_var = self.get_name()
        fig.add_script(f"var {layer_var} = L.markerClusterGroup({tojson(self.kwargs)});")
        if self.show:
            fig.add_script(f"{layer_var}.addTo({mvar});")

        # Render children markers the slow way if present
        # (kept for compatibility)
        self.render_children(**kwargs)

        # Bulk markers in a compact loop
        if self._locations:
            locs = self._locations
            fig.add_script(f"var {layer_var}_locs = {tojson(locs)};")
            if isinstance(self._popup, list) or isinstance(self._popup, tuple):
                fig.add_script(f"var {layer_var}_popups = {tojson(list(self._popup))};")
                fig.add_script(
                    f"for (var i=0;i<{layer_var}_locs.length;i++) {{"
                    f"var m=L.marker({layer_var}_locs[i]);"
                    f"var p={layer_var}_popups[i];"
                    f"if (p!==null && p!==undefined) m.bindPopup(String(p));"
                    f"{layer_var}.addLayer(m);"
                    f"}}"
                )
            elif isinstance(self._popup, str):
                fig.add_script(
                    f"for (var i=0;i<{layer_var}_locs.length;i++) {{"
                    f"var m=L.marker({layer_var}_locs[i]).bindPopup({tojson(self._popup)});"
                    f"{layer_var}.addLayer(m);"
                    f"}}"
                )
            else:
                fig.add_script(
                    f"for (var i=0;i<{layer_var}_locs.length;i++) {{"
                    f"{layer_var}.addLayer(L.marker({layer_var}_locs[i]));"
                    f"}}"
                )

        return ""