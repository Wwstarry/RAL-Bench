from __future__ import annotations

from typing import Any, Optional

from .elements import Element, Figure, MacroElement, _HtmlContainer
from .utilities import json_dumps, normalize_location


LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"

PROVIDERS: dict[str, tuple[str, str]] = {
    "OpenStreetMap": (
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    ),
}


class Layer(MacroElement):
    _name = "layer"

    def __init__(
        self,
        name: Optional[str] = None,
        overlay: bool = True,
        control: bool = True,
        show: bool = True,
    ) -> None:
        super().__init__()
        self.layer_name = name
        self.overlay = overlay
        self.control = control
        self.show = show

    def get_control_name(self) -> str:
        return self.layer_name or self.__class__.__name__


class Map(MacroElement):
    _name = "map"

    def __init__(
        self,
        location=(0, 0),
        zoom_start: int = 10,
        tiles: Any = "OpenStreetMap",
        width: str = "100%",
        height: str = "100%",
        control_scale: bool = False,
        prefer_canvas: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.location = normalize_location(location)
        self.zoom_start = int(zoom_start)
        self.width = width
        self.height = height
        self.control_scale = bool(control_scale)
        self.prefer_canvas = bool(prefer_canvas)
        self.options = dict(kwargs)

        self._figure: Optional[Figure] = None

        # Layer registry for LayerControl
        self._base_layers: dict[str, str] = {}
        self._overlays: dict[str, str] = {}

        # Map container div
        self._div = _HtmlContainer(
            "div",
            attrs={
                "id": self.get_name(),
                "style": f"width:{self.width};height:{self.height};",
            },
        )

        if tiles is not None:
            TileLayer(tiles=tiles, name=str(tiles), overlay=False, control=True, show=True).add_to(self)

    def add_child(self, child: Element, name: Optional[str] = None, index: Optional[int] = None) -> Element:
        return super().add_child(child, name=name, index=index)

    def add_to(self, parent: Element) -> "Map":
        parent.add_child(self)
        return self

    def get_root(self) -> Figure:
        root = super().get_root()
        if isinstance(root, Figure):
            self._figure = root
            return root
        # Not attached: create a figure and attach
        fig = Figure()
        fig.add_child(self)
        self._figure = fig
        return fig

    def _ensure_assets(self, fig: Figure) -> None:
        if fig.add_asset("leaflet.css"):
            fig.header.add_child(_Raw(f'<link rel="stylesheet" href="{LEAFLET_CSS}"/>'))
        if fig.add_asset("leaflet.js"):
            fig.header.add_child(_Raw(f'<script src="{LEAFLET_JS}"></script>'))

    def _template(self) -> str:
        fig = self.get_root()
        self._ensure_assets(fig)

        # Place container in body once
        if self._div.parent is None:
            fig.html.add_child(self._div)

        # Map init script
        opts = {}
        if self.control_scale:
            opts["controlScale"] = True
        if self.prefer_canvas:
            opts["preferCanvas"] = True
        opts.update(self.options)

        parts = []
        parts.append(f"var {self.get_name()} = L.map({json_dumps(self.get_name())}, ")
        parts.append(json_dumps({"center": self.location, "zoom": self.zoom_start, **opts}))
        parts.append(");\n")
        return "".join(parts)


class _Raw(Element):
    _name = "raw"

    def __init__(self, html: str) -> None:
        super().__init__()
        self.html = html

    def render(self, **kwargs: Any) -> str:
        return self.html


class TileLayer(Layer):
    _name = "tile_layer"

    def __init__(
        self,
        tiles: str = "OpenStreetMap",
        name: Optional[str] = None,
        attr: Optional[str] = None,
        overlay: bool = False,
        control: bool = True,
        show: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name or str(tiles), overlay=overlay, control=control, show=show)
        self.tiles = tiles
        self.attr = attr
        self.kwargs = kwargs

    def _resolve(self) -> tuple[str, str]:
        if self.tiles in PROVIDERS:
            url, attr = PROVIDERS[self.tiles]
            return url, self.attr or attr
        # custom template url
        return self.tiles, self.attr or ""

    def _template(self) -> str:
        m = self._find_map()
        fig = m.get_root()
        m._ensure_assets(fig)

        url, attr = self._resolve()
        opts = dict(self.kwargs)
        if attr:
            opts["attribution"] = attr
        js = []
        js.append(f"var {self.get_name()} = L.tileLayer({json_dumps(url)},{json_dumps(opts)});\n")

        if self.control:
            (m._overlays if self.overlay else m._base_layers)[self.get_control_name()] = self.get_name()

        if self.show:
            js.append(f"{self.get_name()}.addTo({m.get_name()});\n")
        return "".join(js)

    def _find_map(self) -> Map:
        node: Optional[Element] = self.parent
        while node is not None and not isinstance(node, Map):
            node = node.parent
        if node is None:
            raise ValueError("TileLayer must be added to a Map before rendering")
        return node


class LayerControl(MacroElement):
    _name = "layer_control"

    def __init__(
        self,
        position: str = "topright",
        collapsed: bool = True,
        autoZIndex: bool = True,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.position = position
        self.collapsed = collapsed
        self.autoZIndex = autoZIndex
        self.kwargs = kwargs

    def _template(self) -> str:
        m = self._find_map()
        fig = m.get_root()
        m._ensure_assets(fig)

        base = "{" + ",".join(f"{json_dumps(k)}:{v}" for k, v in m._base_layers.items()) + "}"
        over = "{" + ",".join(f"{json_dumps(k)}:{v}" for k, v in m._overlays.items()) + "}"
        opts = {"position": self.position, "collapsed": self.collapsed, "autoZIndex": self.autoZIndex}
        opts.update(self.kwargs)
        return f"L.control.layers({base},{over},{json_dumps(opts)}).addTo({m.get_name()});\n"

    def _find_map(self) -> Map:
        node: Optional[Element] = self.parent
        while node is not None and not isinstance(node, Map):
            node = node.parent
        if node is None:
            raise ValueError("LayerControl must be added to a Map before rendering")
        return node