from __future__ import annotations

from typing import Any

from .map import Element
from .utilities import js_var_name, to_json


_OSM_URL = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
_OSM_ATTR = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'


class TileLayer(Element):
    def __init__(
        self,
        tiles: str = "OpenStreetMap",
        name: str | None = None,
        attr: str | None = None,
        overlay: bool = False,
        control: bool = True,
        show: bool = True,
        **kwargs: Any,
    ):
        super().__init__(name="tile_layer")
        self.tiles = tiles
        self.layer_name = name if name is not None else None
        self.attr = attr
        self.overlay = bool(overlay)
        self.control = bool(control)
        self.show = bool(show)
        self.kwargs = dict(kwargs)

    def add_to(self, parent: Element) -> "TileLayer":
        parent.add_child(self)
        return self

    def _resolve(self):
        tiles = self.tiles
        if tiles == "OpenStreetMap":
            url = _OSM_URL
            attr = self.attr if self.attr is not None else _OSM_ATTR
            return url, attr
        if isinstance(tiles, str) and ("{x}" in tiles and "{y}" in tiles and "{z}" in tiles):
            url = tiles
            attr = self.attr if self.attr is not None else ""
            return url, attr
        # Fallback: treat as URL if string, else stringified.
        url = str(tiles)
        attr = self.attr if self.attr is not None else ""
        return url, attr

    def _js_var(self) -> str:
        return js_var_name("tile_layer", self._id)

    def render(self, **kwargs) -> str:
        parent_map = kwargs.get("parent_map")
        if not parent_map:
            parent_map = "map"

        url, attr = self._resolve()
        options = dict(self.kwargs)
        if attr:
            options["attribution"] = attr

        var_ = self._js_var()
        lines = [f"var {var_} = L.tileLayer({to_json(url)}, {to_json(options)});"]
        if self.show:
            lines.append(f"{var_}.addTo({parent_map});")
        return "\n".join(lines)