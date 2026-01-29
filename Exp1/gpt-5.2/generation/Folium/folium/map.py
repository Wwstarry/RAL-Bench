from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

from .elements import Figure, MacroElement
from .util import get_name, tojson


LeafletPos = Union[Tuple[float, float], List[float]]


_LEAFLET_CSS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
_LEAFLET_JS = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"


class Map(MacroElement):
    """
    Minimal folium.Map compatible object.
    """
    def __init__(
        self,
        location: LeafletPos = (0.0, 0.0),
        zoom_start: int = 10,
        tiles: Optional[Union[str, bool]] = "OpenStreetMap",
        width: str = "100%",
        height: str = "100%",
        control_scale: bool = False,
        prefer_canvas: bool = False,
        **kwargs: Any,
    ):
        super().__init__(name="map")
        self.location = [float(location[0]), float(location[1])]
        self.zoom_start = int(zoom_start)
        self.width = width
        self.height = height
        self.control_scale = control_scale
        self.prefer_canvas = prefer_canvas
        self.options: Dict[str, Any] = {}
        self.options.update(kwargs)

        self._id = get_name("map")
        self._tile_setting = tiles
        self._has_layer_control = False

        # layer bookkeeping
        self._layers: List[MacroElement] = []

    def get_name(self) -> str:
        return self._id

    def add_child(self, child: MacroElement, name: Optional[str] = None) -> MacroElement:
        super().add_child(child, name=name)
        # Keep list of layers for LayerControl
        self._layers.append(child)
        return child

    def get_root(self) -> Figure:
        root = super().get_root()
        if not isinstance(root, Figure):
            # Create a root figure if none exists
            fig = Figure(width=self.width, height=self.height)
            fig.add_child(self)
            return fig
        return root

    def _ensure_leaflet_includes(self, fig: Figure) -> None:
        fig.add_header(f'<link rel="stylesheet" href="{_LEAFLET_CSS}"/>')
        fig.add_header(f'<script src="{_LEAFLET_JS}"></script>')

    def render(self, **kwargs: Any) -> str:
        fig = self.get_root()
        self._ensure_leaflet_includes(fig)

        # Create map div
        div_id = self._id
        fig.add_html(
            f'<div id="{div_id}" style="width:{self.width};height:{self.height};"></div>'
        )

        # Map initialization JS
        opts: Dict[str, Any] = dict(self.options)
        if self.prefer_canvas:
            opts["preferCanvas"] = True

        js_opts = tojson(opts)
        fig.add_script(
            f"var {div_id} = L.map('{div_id}', {js_opts}).setView({tojson(self.location)}, {self.zoom_start});"
        )
        if self.control_scale:
            fig.add_script(f"L.control.scale().addTo({div_id});")

        # Default tiles
        if self._tile_setting not in (None, False):
            from .features import TileLayer

            TileLayer(self._tile_setting).add_to(self)

        # Render children/layers; they append JS to fig
        self.render_children(**kwargs)

        # If a layer control exists as child, it will render itself.
        # Otherwise do nothing.
        return fig.render(**kwargs)