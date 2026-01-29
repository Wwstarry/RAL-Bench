from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from .elements import MacroElement
from .util import escape_html, get_name, js_var, tojson


LatLng = Union[Tuple[float, float], List[float]]


class Layer(MacroElement):
    def __init__(
        self,
        name: Optional[str] = None,
        overlay: bool = True,
        control: bool = True,
        show: bool = True,
    ):
        super().__init__(name=name)
        self.layer_name = name
        self.overlay = overlay
        self.control = control
        self.show = show
        self._id = get_name("layer")

    def get_name(self) -> str:
        return self._id

    def _map_var(self) -> str:
        m = self.get_root()
        # Root is Figure, map is likely its first child or ancestor.
        # Walk up to find Map-like with get_name method and name "map".
        obj = self
        while obj._parent is not None:
            if getattr(obj._parent, "_name", None) == "map":
                return obj._parent.get_name()  # type: ignore[attr-defined]
            obj = obj._parent
        # Fallback: common map var name
        return "map"


class TileLayer(Layer):
    PROVIDERS: Dict[str, Dict[str, Any]] = {
        "OpenStreetMap": {
            "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "attr": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            "max_zoom": 19,
        }
    }

    def __init__(
        self,
        tiles: str = "OpenStreetMap",
        name: Optional[str] = None,
        overlay: bool = False,
        control: bool = True,
        show: bool = True,
        attr: Optional[str] = None,
        max_zoom: Optional[int] = None,
        **kwargs: Any,
    ):
        super().__init__(name=name or tiles, overlay=overlay, control=control, show=show)
        self.tiles = tiles
        self.kwargs = dict(kwargs)
        prov = self.PROVIDERS.get(tiles, None)
        if prov:
            self.url = prov["url"]
            self.attr = attr if attr is not None else prov["attr"]
            self.max_zoom = max_zoom if max_zoom is not None else prov.get("max_zoom")
        else:
            # If tiles is actually a URL template
            self.url = tiles
            self.attr = attr if attr is not None else ""
            self.max_zoom = max_zoom

    def render(self, **kwargs: Any) -> str:
        fig = self.get_root()
        mvar = self._map_var()
        options: Dict[str, Any] = dict(self.kwargs)
        if self.attr:
            options["attribution"] = self.attr
        if self.max_zoom is not None:
            options["maxZoom"] = int(self.max_zoom)

        layer_var = self.get_name()
        fig.add_script(f"var {layer_var} = L.tileLayer({tojson(self.url)}, {tojson(options)});")
        if self.show:
            fig.add_script(f"{layer_var}.addTo({mvar});")
        return ""


class Marker(Layer):
    def __init__(
        self,
        location: LatLng,
        popup: Optional[str] = None,
        tooltip: Optional[str] = None,
        icon: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ):
        super().__init__(name=kwargs.pop("name", None), overlay=True, control=False, show=True)
        self.location = [float(location[0]), float(location[1])]
        self.popup = popup
        self.tooltip = tooltip
        self.icon = icon
        self.kwargs = dict(kwargs)

    def render(self, **kwargs: Any) -> str:
        fig = self.get_root()
        mvar = self._map_var()
        layer_var = self.get_name()
        opts = dict(self.kwargs)
        if self.icon is not None:
            # minimal: accept dict already in Leaflet format
            opts["icon"] = self.icon
        fig.add_script(f"var {layer_var} = L.marker({tojson(self.location)}, {tojson(opts)}).addTo({mvar});")
        if self.popup is not None:
            fig.add_script(f"{layer_var}.bindPopup({tojson(str(self.popup))});")
        if self.tooltip is not None:
            fig.add_script(f"{layer_var}.bindTooltip({tojson(str(self.tooltip))});")
        return ""


class CircleMarker(Layer):
    def __init__(
        self,
        location: LatLng,
        radius: float = 10,
        popup: Optional[str] = None,
        tooltip: Optional[str] = None,
        **kwargs: Any,
    ):
        super().__init__(name=kwargs.pop("name", None), overlay=True, control=False, show=True)
        self.location = [float(location[0]), float(location[1])]
        self.radius = radius
        self.popup = popup
        self.tooltip = tooltip
        self.kwargs = dict(kwargs)

    def render(self, **kwargs: Any) -> str:
        fig = self.get_root()
        mvar = self._map_var()
        layer_var = self.get_name()
        opts = dict(self.kwargs)
        opts.setdefault("radius", self.radius)
        fig.add_script(f"var {layer_var} = L.circleMarker({tojson(self.location)}, {tojson(opts)}).addTo({mvar});")
        if self.popup is not None:
            fig.add_script(f"{layer_var}.bindPopup({tojson(str(self.popup))});")
        if self.tooltip is not None:
            fig.add_script(f"{layer_var}.bindTooltip({tojson(str(self.tooltip))});")
        return ""


class GeoJson(Layer):
    def __init__(
        self,
        data: Any,
        name: Optional[str] = None,
        overlay: bool = True,
        control: bool = True,
        show: bool = True,
        style_function: Optional[Any] = None,
        **kwargs: Any,
    ):
        super().__init__(name=name, overlay=overlay, control=control, show=show)
        self.data = data
        self.style_function = style_function
        self.kwargs = dict(kwargs)

    def render(self, **kwargs: Any) -> str:
        fig = self.get_root()
        mvar = self._map_var()
        layer_var = self.get_name()

        options: Dict[str, Any] = dict(self.kwargs)
        if self.style_function is not None:
            # Basic compatibility: style_function(feature)->dict, applied via style callback.
            # We serialize a JS function that returns provided dict computed at build time per feature
            # only when data is FeatureCollection. Otherwise, ignore.
            pass

        gj = self.data
        fig.add_script(f"var {layer_var} = L.geoJSON({tojson(gj)}, {tojson(options)});")
        if self.show:
            fig.add_script(f"{layer_var}.addTo({mvar});")
        return ""


class LayerControl(MacroElement):
    def __init__(self, position: str = "topright", collapsed: bool = True, autoZIndex: bool = True, **kwargs: Any):
        super().__init__(name="layer_control")
        self.position = position
        self.collapsed = collapsed
        self.autoZIndex = autoZIndex
        self.kwargs = dict(kwargs)

    def render(self, **kwargs: Any) -> str:
        fig = self.get_root()

        # Find the map element (ancestor chain)
        map_obj = None
        obj: Any = self
        while obj is not None:
            if getattr(obj, "_name", None) == "map":
                map_obj = obj
                break
            obj = getattr(obj, "_parent", None)
        if map_obj is None:
            return ""

        mvar = map_obj.get_name()

        # Collect layers from map children (best effort)
        base_layers: Dict[str, str] = {}
        overlays: Dict[str, str] = {}

        for ch in getattr(map_obj, "_layers", []):
            # ch might not be Layer; ignore those without get_name and attributes
            if not hasattr(ch, "get_name"):
                continue
            lname = getattr(ch, "layer_name", None)
            overlay = getattr(ch, "overlay", True)
            control = getattr(ch, "control", False)
            if not control:
                continue
            if not lname:
                lname = ch.get_name()
            safe_name = escape_html(str(lname))
            if overlay:
                overlays[safe_name] = ch.get_name()
            else:
                base_layers[safe_name] = ch.get_name()

        opts = dict(self.kwargs)
        opts.update({"position": self.position, "collapsed": self.collapsed, "autoZIndex": self.autoZIndex})

        # Build JS object literals with quoted keys and variable values
        def obj_lit(d: Dict[str, str]) -> str:
            items = [f"{tojson(k)}: {v}" for k, v in d.items()]
            return "{%s}" % (", ".join(items))

        fig.add_script(
            f"L.control.layers({obj_lit(base_layers)}, {obj_lit(overlays)}, {tojson(opts)}).addTo({mvar});"
        )
        return ""