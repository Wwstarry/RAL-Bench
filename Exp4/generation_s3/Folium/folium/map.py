from __future__ import annotations

from collections import OrderedDict
from typing import Any

from .utilities import generate_id, js_var_name, to_json, validate_location
from .template import (
    LEAFLET_CSS,
    LEAFLET_JS,
    MARKERCLUSTER_CSS,
    MARKERCLUSTER_CSS_DEFAULT,
    MARKERCLUSTER_JS,
    html_page,
)
from .raster_layers import TileLayer


class Element:
    def __init__(self, name: str | None = None):
        self._name = name if name is not None else self.__class__.__name__
        self._id = generate_id()
        self._children: "OrderedDict[str, Element]" = OrderedDict()
        self._parent: Element | None = None

    def add_child(self, child: "Element", name: str | None = None, index: int | None = None) -> "Element":
        if name is None:
            name = f"{child._name}_{child._id}"
        child._parent = self

        if index is None or index >= len(self._children):
            self._children[name] = child
        else:
            items = list(self._children.items())
            items.insert(index, (name, child))
            self._children = OrderedDict(items)
        return self

    def add_to(self, parent: "Element") -> "Element":
        parent.add_child(self)
        return self

    def get_root(self) -> "Element":
        cur: Element = self
        while getattr(cur, "_parent", None) is not None:
            cur = cur._parent  # type: ignore[assignment]
        return cur

    def _js_var(self) -> str:
        return js_var_name(self._name, self._id)

    def render(self, **kwargs) -> str:
        # Default: render children only.
        parts: list[str] = []
        for child in self._children.values():
            parts.append(child.render(**kwargs))
        return "\n".join(p for p in parts if p)


class Map(Element):
    def __init__(
        self,
        location: list[float] | tuple[float, float] | None = None,
        zoom_start: int = 10,
        tiles: str | None = "OpenStreetMap",
        attr: str | None = None,
        control_scale: bool = False,
        prefer_canvas: bool = False,
        zoom_control: bool = True,
        **kwargs: Any,
    ):
        super().__init__(name="map")
        self.location = validate_location(location) if location is not None else [0.0, 0.0]
        self.zoom_start = int(zoom_start)
        self.tiles = tiles
        self.attr = attr
        self.control_scale = bool(control_scale)
        self.prefer_canvas = bool(prefer_canvas)
        self.zoom_control = bool(zoom_control)
        self.width = kwargs.get("width", "100%")
        self.height = kwargs.get("height", "100%")
        self._include_markercluster = False

        if tiles is not None:
            TileLayer(tiles=tiles, name=str(tiles), attr=attr).add_to(self)

    def get_root(self) -> "Map":
        return self

    def _collect_layer_control_entries(self):
        base_layers: list[tuple[str, str]] = []
        overlays: list[tuple[str, str]] = []

        def walk(el: Element):
            for ch in el._children.values():
                walk(ch)

            name = getattr(el, "layer_name", None)
            control = getattr(el, "control", False)
            overlay = getattr(el, "overlay", True)
            js_var = getattr(el, "_js_var", None)
            if callable(js_var) and control and name is not None:
                entry = (str(name), el._js_var())
                if overlay:
                    overlays.append(entry)
                else:
                    base_layers.append(entry)

        walk(self)
        return base_layers, overlays

    def _scan_for_markercluster(self):
        def walk(el: Element) -> bool:
            from .plugins.marker_cluster import MarkerCluster  # local import

            for ch in el._children.values():
                if isinstance(ch, MarkerCluster):
                    return True
                if walk(ch):
                    return True
            return False

        self._include_markercluster = walk(self)

    def render(self, **kwargs) -> str:
        self._scan_for_markercluster()

        map_div_id = f"map_{self._id}"
        map_var = self._js_var()

        head_extras = [
            f'<link rel="stylesheet" href="{LEAFLET_CSS}"/>',
            f'<script src="{LEAFLET_JS}"></script>',
        ]
        if self._include_markercluster:
            head_extras.extend(
                [
                    f'<link rel="stylesheet" href="{MARKERCLUSTER_CSS}"/>',
                    f'<link rel="stylesheet" href="{MARKERCLUSTER_CSS_DEFAULT}"/>',
                    f'<script src="{MARKERCLUSTER_JS}"></script>',
                ]
            )

        body = f'<div id="{map_div_id}" style="width: {self.width}; height: {self.height};"></div>'

        map_options = {
            "zoomControl": self.zoom_control,
            "preferCanvas": self.prefer_canvas,
        }
        # controlScale is a control; minimal: include after map init if requested
        map_init = [
            f"var {map_var} = L.map({to_json(map_div_id)}, {to_json(map_options)}).setView({to_json(self.location)}, {int(self.zoom_start)});"
        ]
        if self.control_scale:
            map_init.append(f"L.control.scale().addTo({map_var});")

        # Render children JS in insertion order.
        child_js: list[str] = []
        for child in self._children.values():
            child_js.append(child.render(parent_map=map_var))

        script = "\n".join([*map_init, *[s for s in child_js if s]])

        return html_page("Folium Map", head_extras, body, script)