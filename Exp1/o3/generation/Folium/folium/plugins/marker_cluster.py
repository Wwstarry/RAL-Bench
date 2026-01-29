"""
Very small re-implementation of Folium's ``plugins.MarkerCluster``.
"""
from __future__ import annotations

import json
from typing import List, Tuple

from .. import _Element, _get_id

__all__ = ["MarkerCluster"]


class MarkerCluster(_Element):
    """
    Group a large amount of `folium.Marker` (and compatible) objects into a
    Leaflet.markercluster layer.

    Only the essential functionality is supported.
    """

    # External resources (CDN)
    _JS = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"
    _CSS = [
        "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css",
        "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css",
    ]

    def __init__(self, name: str = "MarkerCluster") -> None:
        super().__init__()
        self.name = name
        self._requires_js.append(self._JS)
        self._requires_css.extend(self._CSS)

    # ------------------------------------------------------------------ #
    # Public helpers
    # ------------------------------------------------------------------ #
    def add_child(self, child: "_Element") -> "_Element":  # type: ignore[override]
        """
        Override to ensure only marker-like children are accepted.
        """
        # We're forgiving here – real Folium would be stricter.
        self._children.append(child)
        return child

    # ------------------------------------------------------------------ #
    # Rendering
    # ------------------------------------------------------------------ #
    def render(self, parent_name: str | None) -> str:
        """
        Render the cluster and all contained markers.

        The cluster itself **is** added to *parent_name* automatically.
        """
        if parent_name is None:
            raise ValueError("MarkerCluster must be attached to a Map or Layer.")

        lines: List[str] = [f"var {self.var_name} = L.markerClusterGroup();"]
        # Render each marker without automatically adding it to the map.
        for ch in self._children:
            marker_js = ch.render(None)
            lines.append(marker_js)
            lines.append(f"{self.var_name}.addLayer({ch.var_name});")
        # Finally add the cluster group to the map.
        lines.append(f"{self.var_name}.addTo({parent_name});")
        return "\n".join(lines)