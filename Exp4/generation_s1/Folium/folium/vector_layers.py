from __future__ import annotations

from typing import Any, Optional

from .elements import Element, MacroElement
from .utilities import json_dumps, js_str, normalize_location, read_geojson
from .map import Layer, Map


def _find_map_or_group(node: Optional[Element]) -> Element:
    cur = node
    while cur is not None:
        # Map or plugin group (e.g., MarkerCluster) should be an Element with get_name()
        if isinstance(cur, (Map,)):
            return cur
        # MarkerCluster will be MacroElement subclass with get_name; we treat any MacroElement
        # that is not Map but can host markers as group; it will define _is_group = True.
        if getattr(cur, "_is_group", False):
            return cur
        cur = cur.parent
    raise ValueError("Layer must be added to a Map (or group) before rendering")


class Marker(MacroElement):
    _name = "marker"

    def __init__(
        self,
        location,
        popup: Optional[str] = None,
        tooltip: Optional[str] = None,
        icon: Any = None,
        draggable: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.location = normalize_location(location)
        self.popup = popup
        self.tooltip = tooltip
        self.icon = icon
        self.draggable = draggable
        self.kwargs = kwargs

    def _template(self) -> str:
        parent = _find_map_or_group(self.parent)
        opts = dict(self.kwargs)
        if self.draggable:
            opts["draggable"] = True

        js = []
        js.append(f"var {self.get_name()} = L.marker({json_dumps(self.location)},{json_dumps(opts)}).addTo({parent.get_name()});\n")
        if self.popup is not None:
            js.append(f"{self.get_name()}.bindPopup({js_str(self.popup)});\n")
        if self.tooltip is not None:
            js.append(f"{self.get_name()}.bindTooltip({js_str(self.tooltip)});\n")
        return "".join(js)


class CircleMarker(MacroElement):
    _name = "circle_marker"

    def __init__(
        self,
        location,
        radius: int = 10,
        popup: Optional[str] = None,
        tooltip: Optional[str] = None,
        color: str = "#3388ff",
        weight: int = 3,
        fill: bool = True,
        fill_color: Optional[str] = None,
        fill_opacity: float = 0.2,
        **kwargs: Any,
    ) -> None:
        super().__init__()
        self.location = normalize_location(location)
        self.radius = radius
        self.popup = popup
        self.tooltip = tooltip
        self.options = dict(
            radius=radius,
            color=color,
            weight=weight,
            fill=fill,
            fillColor=fill_color or color,
            fillOpacity=fill_opacity,
        )
        self.options.update(kwargs)

    def _template(self) -> str:
        parent = _find_map_or_group(self.parent)
        js = []
        js.append(
            f"var {self.get_name()} = L.circleMarker({json_dumps(self.location)},{json_dumps(self.options)}).addTo({parent.get_name()});\n"
        )
        if self.popup is not None:
            js.append(f"{self.get_name()}.bindPopup({js_str(self.popup)});\n")
        if self.tooltip is not None:
            js.append(f"{self.get_name()}.bindTooltip({js_str(self.tooltip)});\n")
        return "".join(js)


class GeoJson(Layer):
    _name = "geo_json"

    def __init__(
        self,
        data: Any,
        name: Optional[str] = None,
        overlay: bool = True,
        control: bool = True,
        show: bool = True,
        style_function: Any = None,
        highlight_function: Any = None,
        tooltip: Optional[str] = None,
        popup: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(name=name or "GeoJson", overlay=overlay, control=control, show=show)
        self.data = read_geojson(data)
        self.style_function = style_function
        self.highlight_function = highlight_function
        self.tooltip = tooltip
        self.popup = popup
        self.kwargs = kwargs

    def _constant_style(self) -> Optional[dict]:
        sf = self.style_function
        if sf is None:
            return None
        if isinstance(sf, dict):
            return sf
        if callable(sf):
            # Try first feature as constant probe
            try:
                feat = None
                if isinstance(self.data, dict) and self.data.get("type") == "FeatureCollection":
                    feats = self.data.get("features") or []
                    if feats:
                        feat = feats[0]
                if feat is None:
                    feat = {"type": "Feature", "properties": {}, "geometry": None}
                out = sf(feat)
                if isinstance(out, dict):
                    return out
            except Exception:
                return None
        return None

    def _template(self) -> str:
        m = self._find_map()
        fig = m.get_root()
        m._ensure_assets(fig)

        opts = dict(self.kwargs)
        style = self._constant_style()
        if style is not None:
            opts["style"] = style

        js = []
        js.append(f"var {self.get_name()}_data = {json_dumps(self.data)};\n")
        js.append(f"var {self.get_name()} = L.geoJSON({self.get_name()}_data,{json_dumps(opts)});\n")

        if self.tooltip is not None:
            js.append(
                f"{self.get_name()}.eachLayer(function(l){{l.bindTooltip({js_str(self.tooltip)});}});\n"
            )
        if self.popup is not None:
            js.append(
                f"{self.get_name()}.eachLayer(function(l){{l.bindPopup({js_str(self.popup)});}});\n"
            )

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
            raise ValueError("GeoJson must be added to a Map before rendering")
        return node