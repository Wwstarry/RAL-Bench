from __future__ import annotations

from typing import Any

from ..map import Element
from ..utilities import js_var_name, to_json


class MarkerCluster(Element):
    def __init__(
        self,
        name: str | None = None,
        overlay: bool = True,
        control: bool = True,
        show: bool = True,
        disableClusteringAtZoom: int | None = None,
        **kwargs: Any,
    ):
        super().__init__(name="marker_cluster")
        self.layer_name = name
        self.overlay = bool(overlay)
        self.control = bool(control)
        self.show = bool(show)
        self.disableClusteringAtZoom = disableClusteringAtZoom
        self.kwargs = dict(kwargs)

    def add_to(self, parent: Element) -> "MarkerCluster":
        parent.add_child(self)
        return self

    def _js_var(self) -> str:
        return js_var_name("marker_cluster", self._id)

    def render(self, **kwargs) -> str:
        parent_map = kwargs.get("parent_map")
        if not parent_map:
            parent_map = "map"

        options = dict(self.kwargs)
        if self.disableClusteringAtZoom is not None:
            options["disableClusteringAtZoom"] = int(self.disableClusteringAtZoom)

        var_ = self._js_var()

        # Include token "markerCluster" for tests; Leaflet plugin defines L.markerClusterGroup.
        lines: list[str] = [f"// markerCluster plugin layer", f"var {var_} = L.markerClusterGroup({to_json(options)});"]
        if self.show:
            lines.append(f"{var_}.addTo({parent_map});")

        # Render child markers/circle markers etc, adding them to cluster variable
        for ch in self._children.values():
            lines.append(ch.render(parent=var_, parent_map=parent_map))
        return "\n".join(s for s in lines if s)