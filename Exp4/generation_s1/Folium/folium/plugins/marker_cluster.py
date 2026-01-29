from __future__ import annotations

from typing import Any, Optional

from ..elements import Element, MacroElement, _Raw
from ..utilities import json_dumps
from ..map import Layer, Map


MC_CSS = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"
MC_CSS_DEFAULT = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css"
MC_JS = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"


class MarkerCluster(Layer):
    _name = "marker_cluster"
    _is_group = True  # allow markers to addTo(this group)

    def __init__(
        self,
        name: str = "MarkerCluster",
        overlay: bool = True,
        control: bool = True,
        show: bool = True,
        options: Optional[dict] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name, overlay=overlay, control=control, show=show)
        self.options = options or {}
        self.options.update(kwargs)

    def _find_map(self) -> Map:
        node: Optional[Element] = self.parent
        while node is not None and not isinstance(node, Map):
            node = node.parent
        if node is None:
            raise ValueError("MarkerCluster must be added to a Map before rendering")
        return node

    def _ensure_assets(self, fig) -> None:
        if fig.add_asset("leaflet.markercluster.css"):
            fig.header.add_child(_Raw(f'<link rel="stylesheet" href="{MC_CSS}"/>'))
            fig.header.add_child(_Raw(f'<link rel="stylesheet" href="{MC_CSS_DEFAULT}"/>'))
        if fig.add_asset("leaflet.markercluster.js"):
            fig.header.add_child(_Raw(f'<script src="{MC_JS}"></script>'))

    def _template(self) -> str:
        m = self._find_map()
        fig = m.get_root()
        m._ensure_assets(fig)
        self._ensure_assets(fig)

        js = []
        js.append(f"var {self.get_name()} = L.markerClusterGroup({json_dumps(self.options)});\n")

        # Register single overlay in control
        if self.control:
            (m._overlays if self.overlay else m._base_layers)[self.get_control_name()] = self.get_name()

        # Render child markers (they will addTo(cluster_var) because of _is_group)
        for child in self._children.values():
            js.append(child.render())

        if self.show:
            js.append(f"{self.get_name()}.addTo({m.get_name()});\n")
        return "".join(js)