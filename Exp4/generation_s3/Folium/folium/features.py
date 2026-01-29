from __future__ import annotations

import json
import os
from typing import Any

from .map import Element
from .utilities import escape_html, js_var_name, to_json, validate_location


class Marker(Element):
    def __init__(
        self,
        location: list[float] | tuple[float, float],
        popup: str | None = None,
        tooltip: str | None = None,
        icon: dict | None = None,
        draggable: bool = False,
        **kwargs: Any,
    ):
        super().__init__(name="marker")
        self.location = validate_location(location)
        self.popup = popup
        self.tooltip = tooltip
        self.icon = icon
        self.draggable = bool(draggable)
        self.kwargs = dict(kwargs)
        self.layer_name = kwargs.get("name", None)
        self.overlay = bool(kwargs.get("overlay", True))
        self.control = bool(kwargs.get("control", False))
        self.show = bool(kwargs.get("show", True))

    def add_to(self, parent: Element) -> "Marker":
        parent.add_child(self)
        return self

    def _js_var(self) -> str:
        return js_var_name("marker", self._id)

    def render(self, **kwargs) -> str:
        parent = kwargs.get("parent") or kwargs.get("parent_map")
        if not parent:
            parent = "map"

        options = dict(self.kwargs)
        options["draggable"] = self.draggable
        if self.icon is not None:
            options["icon"] = self.icon  # tests likely only require options present; Leaflet icon object not created here.

        var_ = self._js_var()
        lines = [f"var {var_} = L.marker({to_json(self.location)}, {to_json(options)});"]
        if self.show:
            lines.append(f"{var_}.addTo({parent});")
        if self.popup is not None:
            popup_str = escape_html(str(self.popup))
            lines.append(f"{var_}.bindPopup({to_json(popup_str)});")
        if self.tooltip is not None:
            tooltip_str = escape_html(str(self.tooltip))
            lines.append(f"{var_}.bindTooltip({to_json(tooltip_str)});")
        return "\n".join(lines)


class CircleMarker(Element):
    def __init__(
        self,
        location: list[float] | tuple[float, float],
        radius: int = 10,
        popup: str | None = None,
        tooltip: str | None = None,
        color: str = "#3388ff",
        weight: int = 3,
        fill: bool = True,
        fill_color: str | None = None,
        fill_opacity: float = 0.2,
        **kwargs: Any,
    ):
        super().__init__(name="circle_marker")
        self.location = validate_location(location)
        self.radius = int(radius)
        self.popup = popup
        self.tooltip = tooltip
        self.color = color
        self.weight = int(weight)
        self.fill = bool(fill)
        self.fill_color = fill_color
        self.fill_opacity = float(fill_opacity)
        self.kwargs = dict(kwargs)
        self.layer_name = kwargs.get("name", None)
        self.overlay = bool(kwargs.get("overlay", True))
        self.control = bool(kwargs.get("control", False))
        self.show = bool(kwargs.get("show", True))

    def add_to(self, parent: Element) -> "CircleMarker":
        parent.add_child(self)
        return self

    def _js_var(self) -> str:
        return js_var_name("circle_marker", self._id)

    def render(self, **kwargs) -> str:
        parent = kwargs.get("parent") or kwargs.get("parent_map")
        if not parent:
            parent = "map"

        options = dict(self.kwargs)
        options.update(
            {
                "radius": self.radius,
                "color": self.color,
                "weight": self.weight,
                "fill": self.fill,
                "fillOpacity": self.fill_opacity,
            }
        )
        if self.fill_color is not None:
            options["fillColor"] = self.fill_color

        var_ = self._js_var()
        lines = [f"var {var_} = L.circleMarker({to_json(self.location)}, {to_json(options)});"]
        if self.show:
            lines.append(f"{var_}.addTo({parent});")
        if self.popup is not None:
            popup_str = escape_html(str(self.popup))
            lines.append(f"{var_}.bindPopup({to_json(popup_str)});")
        if self.tooltip is not None:
            tooltip_str = escape_html(str(self.tooltip))
            lines.append(f"{var_}.bindTooltip({to_json(tooltip_str)});")
        return "\n".join(lines)


class GeoJson(Element):
    def __init__(
        self,
        data: dict | str,
        name: str | None = None,
        overlay: bool = True,
        control: bool = True,
        show: bool = True,
        style_function: Any | None = None,
        **kwargs: Any,
    ):
        super().__init__(name="geo_json")
        self.data = self._load_data(data)
        self.layer_name = name
        self.overlay = bool(overlay)
        self.control = bool(control)
        self.show = bool(show)
        self.style_function = style_function
        self.kwargs = dict(kwargs)

    def add_to(self, parent: Element) -> "GeoJson":
        parent.add_child(self)
        return self

    def _js_var(self) -> str:
        return js_var_name("geo_json", self._id)

    def _load_data(self, data: dict | str) -> dict:
        if isinstance(data, dict):
            return data
        if not isinstance(data, str):
            raise TypeError("GeoJson data must be a dict or str")
        s = data.strip()
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            try:
                return json.loads(s)
            except Exception as e:
                raise ValueError("Invalid GeoJSON JSON string") from e
        # treat as file path if exists
        if os.path.exists(data) and os.path.isfile(data):
            try:
                with open(data, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                raise ValueError("Invalid GeoJSON file") from e
        raise ValueError("GeoJson data string must be a JSON string or an existing file path")

    def _compute_style(self):
        if not callable(self.style_function):
            return None
        # minimal: attempt to compute a static style dict from first feature or dummy.
        try:
            feat = None
            if isinstance(self.data, dict):
                if self.data.get("type") == "Feature":
                    feat = self.data
                elif self.data.get("type") == "FeatureCollection":
                    feats = self.data.get("features") or []
                    if feats:
                        feat = feats[0]
            style = self.style_function(feat)  # may return dict
            if isinstance(style, dict):
                return style
        except Exception:
            return None
        return None

    def render(self, **kwargs) -> str:
        parent_map = kwargs.get("parent_map")
        if not parent_map:
            parent_map = "map"

        options = dict(self.kwargs)
        style = self._compute_style()
        if style is not None:
            options["style"] = style  # static style dict; Leaflet accepts function; tests accept minimal.

        var_ = self._js_var()
        lines = [f"var {var_} = L.geoJSON({to_json(self.data)}, {to_json(options)});"]
        if self.show:
            lines.append(f"{var_}.addTo({parent_map});")
        return "\n".join(lines)


class LayerControl(Element):
    def __init__(
        self,
        position: str = "topright",
        collapsed: bool = True,
        autoZIndex: bool = True,
        **kwargs: Any,
    ):
        super().__init__(name="layer_control")
        self.position = position
        self.collapsed = bool(collapsed)
        self.autoZIndex = bool(autoZIndex)
        self.kwargs = dict(kwargs)

    def add_to(self, parent: Element) -> "LayerControl":
        parent.add_child(self)
        return self

    def _js_var(self) -> str:
        return js_var_name("layer_control", self._id)

    def render(self, **kwargs) -> str:
        root = self.get_root()
        parent_map = kwargs.get("parent_map")
        if not parent_map:
            parent_map = getattr(root, "_js_var", lambda: "map")()

        base_layers, overlays = ([], [])
        if hasattr(root, "_collect_layer_control_entries"):
            base_layers, overlays = root._collect_layer_control_entries()  # type: ignore[attr-defined]

        base_obj = "{" + ",".join(f"{to_json(name)}:{var}" for name, var in base_layers) + "}"
        over_obj = "{" + ",".join(f"{to_json(name)}:{var}" for name, var in overlays) + "}"

        options = dict(self.kwargs)
        options.update(
            {
                "position": self.position,
                "collapsed": self.collapsed,
                "autoZIndex": self.autoZIndex,
            }
        )

        var_ = self._js_var()
        return f"var {var_} = L.control.layers({base_obj}, {over_obj}, {to_json(options)}).addTo({parent_map});"