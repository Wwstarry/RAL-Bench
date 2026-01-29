"""
A very small subset of the `folium` API implemented in pure-Python.

Only the functionality required by the automated test-suite that accompanies
this repository is supported.  The goal is *compatibility*, **not** feature
parity with the real Folium project.

Supported public objects
------------------------
* folium.Map
* folium.Marker
* folium.CircleMarker
* folium.GeoJson
* folium.TileLayer
* folium.LayerControl
* folium.plugins.MarkerCluster   (imported from the ``folium.plugins`` package)

All objects are *pure builders*: they keep a reference to their children and
during rendering produce a piece of JavaScript/HTML that can be executed in a
browser with Leaflet.js available.

No external Python dependencies are required.
"""
from __future__ import annotations

import itertools
import json
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

__all__ = [
    # main map container
    "Map",
    # layers
    "Marker",
    "CircleMarker",
    "GeoJson",
    "TileLayer",
    "LayerControl",
    # plugin namespace
    "plugins",
]

###############################################################################
# Basic ID generation utilities
###############################################################################
_id_counter = itertools.count(0)


def _get_id() -> int:
    """Return a monotonically increasing integer ID."""
    return next(_id_counter)


###############################################################################
# Base classes
###############################################################################


class _Element:
    """
    Base-class for every renderable map element.

    The class only cares about:
      * keeping a reference to children (`_children`)
      * knowing its own *unique* id (`_id`)
      * providing a stub `render(parent_name)` method that returns JavaScript.
    """

    _children: List["_Element"]
    _requires_js: List[str]
    _requires_css: List[str]

    def __init__(self) -> None:
        self._children = []
        self._id = _get_id()
        # Resources (external) required by this element.
        self._requires_js = []
        self._requires_css = []

    # --------------------------------------------------------------------- #
    # Public helpers
    # --------------------------------------------------------------------- #
    def add_child(self, child: "_Element") -> "_Element":
        """Attach *child* to the current element and return it."""
        self._children.append(child)
        return child

    def add_to(self, parent: "_Element") -> "_Element":
        """
        Convenience helper that mirrors Folium's ``obj.add_to(m)`` behaviour.
        """
        parent.add_child(self)
        return self

    # --------------------------------------------------------------------- #
    # Rendering helpers – expected to be overridden by subclasses.
    # --------------------------------------------------------------------- #
    def render(self, parent_name: Optional[str]) -> str:  # noqa: D401
        """
        Return JavaScript (and possibly HTML) needed to instantiate
        the element inside the Leaflet *parent_name* object.

        *parent_name* is the JavaScript variable name of the parent leaf-let
        layer (usually the map instance).  A ``None`` value indicates that the
        element should **not** be automatically added to any parent; this is
        the case for `Marker` objects that are later inserted into a
        `MarkerCluster`.
        """
        return ""

    # --------------------------------------------------------------------- #
    # Resource handling
    # --------------------------------------------------------------------- #
    @property
    def requires_js(self) -> List[str]:
        """Return a list of external JS URLs needed by the element."""
        # Collect resources from children as well – depth first.
        resources: List[str] = list(self._requires_js)
        for ch in self._children:
            resources.extend(ch.requires_js)
        return resources

    @property
    def requires_css(self) -> List[str]:
        """Return a list of external CSS URLs needed by the element."""
        resources: List[str] = list(self._requires_css)
        for ch in self._children:
            resources.extend(ch.requires_css)
        return resources

    # --------------------------------------------------------------------- #
    # Misc
    # --------------------------------------------------------------------- #
    @property
    def var_name(self) -> str:  # noqa: D401
        """Return a unique JavaScript variable name for the element."""
        return f"el_{self._id}"

    # For debugging / %display etc.
    def _repr_html_(self) -> str:  # pragma: no cover
        if hasattr(self, "get_root"):
            return self.get_root().render()
        return f"<{self.__class__.__name__} – not renderable>"


###############################################################################
# Map container
###############################################################################


class Map(_Element):
    """
    The main map container.

    Very small subset of the real ``folium.Map`` implementation.
    """

    def __init__(
        self,
        location: Tuple[float, float] = (0.0, 0.0),
        zoom_start: int = 10,
        tiles: Optional[str] = "OpenStreetMap",
        width: Union[str, int] = "100%",
        height: Union[str, int] = "100%",
    ) -> None:
        super().__init__()
        self.location = location
        self.zoom_start = zoom_start
        self.tiles = tiles
        self.width = f"{width}px" if isinstance(width, int) else str(width)
        self.height = f"{height}px" if isinstance(height, int) else str(height)

    # ------------------------------------------------------------------ #
    # Folium public helpers
    # ------------------------------------------------------------------ #
    def get_root(self) -> "Map":
        """Return *self* – acts like Folium's dummy *Figure* object."""
        return self

    # ------------------------------------------------------------------ #
    # Rendering
    # ------------------------------------------------------------------ #
    def render(self) -> str:  # noqa: C901 – complex, but straightforward
        """
        Produce a **stand-alone** HTML document containing the map and all
        attached layers/plugins.
        """
        base_tiles_init: str = ""
        external_js: List[str] = []
        external_css: List[str] = []

        # If a default tileset is requested we inject it *before* all children
        # so user-added layers can override / be toggled by a `LayerControl`.
        if self.tiles:
            default_tile = TileLayer(self.tiles)
            base_tiles_init, _is_base = default_tile._render_tilelayer(
                self.var_name, add_to_map=True
            )
            # gather external resources
            external_js.extend(default_tile.requires_js)
            external_css.extend(default_tile.requires_css)

        # JavaScript snippets for every child.
        layer_js_snippets: List[str] = []
        # Keep track of base/overlays => needed for LayerControl.
        base_layer_dict_entries: List[str] = []
        overlay_layer_dict_entries: List[str] = []

        # Does the user want a layer control?
        wants_layer_control: bool = any(
            isinstance(ch, LayerControl) for ch in self._children
        )

        for child in self._children:
            # Children may add their own resource requirements
            external_js.extend(child.requires_js)
            external_css.extend(child.requires_css)

            if isinstance(child, TileLayer):
                # TileLayer needs special treatment to decide if it's base or overlay
                js_snip, is_base = child._render_tilelayer(
                    self.var_name, add_to_map=not wants_layer_control
                )
                layer_js_snippets.append(js_snip)
                entry = f"{json.dumps(child.name)}: {child.var_name}"
                if is_base:
                    base_layer_dict_entries.append(entry)
                else:
                    overlay_layer_dict_entries.append(entry)
            elif isinstance(child, LayerControl):
                # No immediate JS – will be rendered at the very end.
                continue
            else:
                layer_js_snippets.append(child.render(self.var_name))
                # If the object advertises a `name` we expose it for layer-control.
                if hasattr(child, "name"):
                    entry = f"{json.dumps(child.name)}: {child.var_name}"
                    overlay_layer_dict_entries.append(entry)

        # De-duplicate resources while keeping order.
        def _unique(seq: Iterable[str]) -> List[str]:
            seen = set()
            out: List[str] = []
            for item in seq:
                if item not in seen:
                    out.append(item)
                    seen.add(item)
            return out

        external_js = _unique(external_js)
        external_css = _unique(external_css)

        # Build the optional `LayerControl` script.
        layer_control_js: str = ""
        if wants_layer_control:
            base_layers_js = "{" + ", ".join(base_layer_dict_entries) + "}"
            overlay_layers_js = "{" + ", ".join(overlay_layer_dict_entries) + "}"
            layer_control_js = (
                f"L.control.layers({base_layers_js}, {overlay_layers_js}).addTo({self.var_name});"
            )

        # Final HTML assembly.
        html_doc = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>folium map</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <!-- Leaflet core -->
  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.3/dist/leaflet.css"
  />
  <script src="https://unpkg.com/leaflet@1.9.3/dist/leaflet.js"></script>
  <!-- Additional CSS -->
  {'  '.join(f'<link rel="stylesheet" href="{href}"/>' for href in external_css)}
  <!-- Additional JS -->
  {'  '.join(f'<script src="{src}"></script>' for src in external_js)}
  <style>
    html, body {{
        height: 100%;
        margin: 0;
    }}
  </style>
</head>
<body>
  <div id="{self.var_name}" style="width:{self.width}; height:{self.height};"></div>

  <script>
    // create the main map object
    var {self.var_name} = L.map("{self.var_name}").setView(
        [{self.location[0]}, {self.location[1]}], {self.zoom_start}
    );

    {base_tiles_init}

    // --- child layers --------------------------------------------------
    {"".join(sn + "\\n" for sn in layer_js_snippets)}

    // --- layer control -------------------------------------------------
    {layer_control_js}
  </script>
</body>
</html>
"""
        return html_doc


###############################################################################
# Leaflet layers
###############################################################################


class Marker(_Element):
    """
    Simple point marker layer.
    """

    def __init__(
        self,
        location: Tuple[float, float],
        popup: Optional[str] = None,
        tooltip: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.location = location
        self.popup = popup
        self.tooltip = tooltip
        self.options = kwargs
        # Expose a name for LayerControl (optional)
        self.name: str = kwargs.get("name", f"Marker {self._id}")

    def render(self, parent_name: Optional[str]) -> str:
        opts = json.dumps(self.options) if self.options else "{}"
        lines = [
            f"var {self.var_name} = L.marker([{self.location[0]}, {self.location[1]}], {opts});"
        ]
        if self.popup is not None:
            lines.append(f"{self.var_name}.bindPopup({json.dumps(str(self.popup))});")
        if self.tooltip is not None:
            lines.append(
                f"{self.var_name}.bindTooltip({json.dumps(str(self.tooltip))});"
            )
        if parent_name:
            lines.append(f"{self.var_name}.addTo({parent_name});")
        return "\n".join(lines)


class CircleMarker(_Element):
    """
    Circle marker – rendered with ``L.circleMarker``.
    """

    def __init__(
        self,
        location: Tuple[float, float],
        radius: int = 10,
        popup: Optional[str] = None,
        color: str = "#3388ff",
        fill_color: Optional[str] = None,
        fill_opacity: float = 0.6,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.location = location
        self.radius = radius
        self.popup = popup
        self.color = color
        self.fill_color = fill_color or color
        self.fill_opacity = fill_opacity
        self.options = kwargs
        self.name: str = kwargs.get("name", f"CircleMarker {self._id}")

    def render(self, parent_name: Optional[str]) -> str:
        opts: Dict[str, Any] = dict(
            radius=self.radius,
            color=self.color,
            fillColor=self.fill_color,
            fillOpacity=self.fill_opacity,
        )
        opts.update(self.options)
        opts_js = json.dumps(opts)
        lines = [
            f"var {self.var_name} = L.circleMarker([{self.location[0]}, {self.location[1]}], {opts_js});"
        ]
        if self.popup is not None:
            lines.append(f"{self.var_name}.bindPopup({json.dumps(str(self.popup))});")
        if parent_name:
            lines.append(f"{self.var_name}.addTo({parent_name});")
        return "\n".join(lines)


class GeoJson(_Element):
    """Render GeoJSON data."""

    def __init__(
        self,
        data: Union[Dict[str, Any], str],
        name: Optional[str] = None,
        style: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__()
        self.data = data
        self.style = style or {}
        self.name: str = name or f"GeoJson {self._id}"

    def render(self, parent_name: Optional[str]) -> str:
        data_js = json.dumps(self.data)
        style_js = json.dumps(self.style)
        lines = [
            f"var {self.var_name} = L.geoJson({data_js}, "
            f"{{style: function(){{return {style_js};}}}});"
        ]
        if parent_name:
            lines.append(f"{self.var_name}.addTo({parent_name});")
        return "\n".join(lines)


class TileLayer(_Element):
    """
    Wrapper around Leaflet's `L.tileLayer`.

    Supports either a well-known provider name (e.g. ``'OpenStreetMap'``) or a
    custom URL template.
    """

    # A *tiny* subset of Leaflet-Providers meta-data.
    _PROVIDERS = {
        "OpenStreetMap": dict(
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">'
            "OpenStreetMap</a> contributors",
        ),
        "Stamen Terrain": dict(
            url="https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
            attribution='Map tiles by <a href="http://stamen.com">Stamen Design</a>',
        ),
    }

    def __init__(
        self,
        tiles: str = "OpenStreetMap",
        name: Optional[str] = None,
        attr: Optional[str] = None,
        overlay: bool = False,
    ) -> None:
        super().__init__()
        self._raw_tiles = tiles
        provider = self._PROVIDERS.get(tiles)
        self.url = provider["url"] if provider else tiles
        self.attribution = provider["attribution"] if provider else (attr or "")
        self.name: str = name or tiles
        self.overlay = overlay

    # ------------------------------------------------------------------ #
    # Internal – render tile layer & tell caller if it's a base layer.
    # ------------------------------------------------------------------ #
    def _render_tilelayer(
        self, map_name: str, *, add_to_map: bool = True
    ) -> Tuple[str, bool]:
        """
        Return ``(js_snippet, is_base_layer)``.

        *is_base_layer* is ``True`` when the layer is **not** flagged as an
        overlay.  The information is useful for ``LayerControl`` generation.
        """
        js = (
            f"var {self.var_name} = L.tileLayer('{self.url}', "
            f"{{attribution: {json.dumps(self.attribution)}}});"
        )
        if add_to_map:
            js += f"\n{self.var_name}.addTo({map_name});"
        return js, not self.overlay


class LayerControl(_Element):
    """
    Dummy placeholder – actual JS is generated by `Map.render` because it needs
    global knowledge about base & overlay layers.
    """

    def __init__(self) -> None:
        super().__init__()

    # No JS on its own.
    def render(self, parent_name: Optional[str]) -> str:  # noqa: D401
        return ""


###############################################################################
# Simple plugin namespace (only MarkerCluster is provided)
###############################################################################
# The plugin lives in its own module to avoid circular imports.
from importlib import import_module as _imp

plugins = _imp("folium.plugins")  # triggers import of folium.plugins.__init__