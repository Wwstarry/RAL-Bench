import json
import itertools
import html

# Internal util to normalize CSS size values
def _css_size(value, default_px=False):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return f"{int(value)}px"
    s = str(value)
    if any(s.endswith(u) for u in ("px", "%", "vh", "vw", "em", "rem")):
        return s
    if default_px:
        try:
            i = int(float(s))
            return f"{i}px"
        except Exception:
            pass
    return s


# Simple id generator for unique JS variable names
_id_counter = itertools.count(1)


class _Renderable:
    def render_js(self, map_var, include_add=True):
        raise NotImplementedError

    def _var_name(self, prefix):
        if not hasattr(self, "_id"):
            self._id = next(_id_counter)
        return f"{prefix}_{self._id}"

    def add_to(self, parent):
        # default behavior: add to a Map
        if hasattr(parent, "add_child"):
            parent.add_child(self)
        else:
            raise TypeError("Cannot add to parent: unsupported type")
        return self


class Map(_Renderable):
    def __init__(self, location=(0.0, 0.0), zoom_start=13, tiles="OpenStreetMap", width="100%", height="100%"):
        self.location = tuple(location) if location is not None else (0.0, 0.0)
        self.zoom_start = zoom_start
        self.width = _css_size(width)
        self.height = _css_size(height)
        self._children = []
        self._has_layer_control = False
        self._needs_markercluster = False
        self._id = next(_id_counter)
        self._map_var = f"map_{self._id}"
        # Base tile layer by default unless tiles is None
        if tiles is not None:
            tl = TileLayer(tiles=tiles, name=str(tiles) if tiles else "Tiles")
            self.add_child(tl)

    def add_child(self, child):
        # set parent linkage
        child._parent = self
        if isinstance(child, LayerControl):
            self._has_layer_control = True
        if hasattr(child, "_sets_markercluster") and getattr(child, "_sets_markercluster"):
            self._needs_markercluster = True
        self._children.append(child)
        return self

    def add_to(self, parent):
        # Map is root, adding to something else not supported
        raise TypeError("Map cannot be added to another object")

    def get_root(self):
        # For Folium compatibility: returns object with render() method
        return self

    def save(self, filepath):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.render())

    # Backwards compatible alias
    def _repr_html_(self):
        return self.render()

    def render_js(self, map_var, include_add=True):
        # Not used; map is root
        return ""

    def render(self):
        # Collect and prepare layer JS definitions
        base_layers = []
        overlay_layers = []
        layer_js_snippets = []

        # Determine default visible base layer (first base layer)
        first_base_var = None

        # Ensure children are processed in order (default tile added first)
        for child in self._children:
            if isinstance(child, TileLayer):
                var_name, js_code = child._layer_js(self._map_var, include_add=False)
                layer_js_snippets.append(js_code)
                name = child.name or f"Base {child._id}"
                base_layers.append((name, var_name, False))  # False: not "added" yet
                if first_base_var is None:
                    first_base_var = var_name
            elif isinstance(child, LayerControl):
                # Render later
                continue
            else:
                # Overlay objects: Marker, CircleMarker, GeoJson, plugins...
                var_name, js_code = child.render_js(self._map_var, include_add=True)
                layer_js_snippets.append(js_code)
                name = getattr(child, "name", None)
                if name is None:
                    # generate a default name based on class and id
                    cname = child.__class__.__name__
                    name = f"{cname} {getattr(child, '_id', next(_id_counter))}"
                overlay_layers.append((name, var_name))

        # Build layer control JS
        layer_control_js = ""
        if self._has_layer_control:
            base_entries = []
            overlay_entries = []
            for name, var_name, _added in base_layers:
                # wrap name in proper JS string
                base_entries.append(f"{json.dumps(name)}: {var_name}")
            for name, var_name in overlay_layers:
                overlay_entries.append(f"{json.dumps(name)}: {var_name}")
            base_dict = "{%s}" % (", ".join(base_entries))
            overlay_dict = "{%s}" % (", ".join(overlay_entries))
            layer_control_js = f"var base_layers = {base_dict}; var overlay_layers = {overlay_dict}; L.control.layers(base_layers, overlay_layers).addTo({self._map_var});"

        # Determine includes for plugins
        extra_css = []
        extra_js = []
        if self._needs_markercluster:
            extra_css.append("https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css")
            extra_css.append("https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.Default.css")
            extra_js.append("https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js")

        width = self.width or "100%"
        height = self.height or "100%"

        # HTML head with Leaflet includes
        head_parts = []
        head_parts.append('<meta charset="utf-8"/>')
        head_parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0"/>')
        head_parts.append('<title>folium map</title>')
        head_parts.append('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />')
        for href in extra_css:
            head_parts.append(f'<link rel="stylesheet" href="{href}" />')
        # Inline style to size the map
        styles = f"""
        <style>
        #{self._map_var} {{
            position: relative;
            width: {html.escape(width)};
            height: {html.escape(height)};
        }}
        </style>
        """.strip()
        head_parts.append(styles)

        # Body: map container and scripts
        body_parts = []
        body_parts.append(f'<div id="{self._map_var}"></div>')
        # Leaflet JS
        body_parts.append('<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>')
        for src in extra_js:
            body_parts.append(f'<script src="{src}"></script>')

        # Map initialization script
        center_json = json.dumps([self.location[0], self.location[1]])
        init_js_lines = []
        init_js_lines.append(f"var {self._map_var} = L.map({json.dumps(self._map_var)}, {{center: {center_json}, zoom: {int(self.zoom_start)}}});")
        # Add default/first base layer
        if first_base_var is not None:
            init_js_lines.append(f"{first_base_var}.addTo({self._map_var});")
        # Add overlay and layer variables JS
        init_js_lines.extend(layer_js_snippets)
        # Layer control
        if layer_control_js:
            init_js_lines.append(layer_control_js)

        body_parts.append("<script>\n" + "\n".join(init_js_lines) + "\n</script>")

        html_doc = "<!DOCTYPE html>\n<html>\n<head>\n" + "\n".join(head_parts) + "\n</head>\n<body>\n" + "\n".join(body_parts) + "\n</body>\n</html>"
        return html_doc


class TileLayer(_Renderable):
    # Recognized simple providers
    _PROVIDERS = {
        "OpenStreetMap": {
            "url": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
            "attribution": '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        },
        "Stamen Terrain": {
            "url": "https://stamen-tiles.a.ssl.fastly.net/terrain/{z}/{x}/{y}.jpg",
            "attribution": 'Map tiles by <a href="http://stamen.com">Stamen</a>, under CC BY 3.0. Data &copy; OSM contributors',
        },
        "CartoDB positron": {
            "url": "https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png",
            "attribution": '&copy; <a href="https://carto.com/attributions">CARTO</a> &copy; OSM contributors',
        },
    }

    def __init__(self, tiles="OpenStreetMap", name=None, attr=None, max_zoom=19):
        self.tiles = tiles
        self.name = name or (str(tiles) if isinstance(tiles, str) else "Tiles")
        self.attr = attr
        self.max_zoom = max_zoom
        self._id = next(_id_counter)

    def _resolve_url_and_attr(self):
        if isinstance(self.tiles, str) and self.tiles in self._PROVIDERS:
            url = self._PROVIDERS[self.tiles]["url"]
            attribution = self.attr if self.attr is not None else self._PROVIDERS[self.tiles]["attribution"]
            return url, attribution
        # Treat tiles as URL template
        url = str(self.tiles)
        attribution = self.attr if self.attr is not None else ""
        return url, attribution

    def _layer_js(self, map_var, include_add=False):
        var_name = f"tilelayer_{self._id}"
        url, attribution = self._resolve_url_and_attr()
        options = {"attribution": attribution, "maxZoom": int(self.max_zoom)}
        opts_js = json.dumps(options)
        js = f"var {var_name} = L.tileLayer({json.dumps(url)}, {opts_js});"
        # Map will add the first base layer itself
        return var_name, js

    def render_js(self, map_var, include_add=True):
        # Provided for uniformity; base layers are handled by Map
        return self._layer_js(map_var, include_add)


class Marker(_Renderable):
    def __init__(self, location, popup=None, name=None):
        self.location = tuple(location)
        self.popup = popup
        self.name = name or "Marker"
        self._id = next(_id_counter)

    def render_js(self, map_var, include_add=True):
        # If parent is a MarkerCluster, it will handle aggregation. In that case, return empty js.
        if hasattr(self, "_parent") and self._parent.__class__.__name__ == "MarkerCluster":
            return f"marker_{self._id}", ""
        var_name = f"marker_{self._id}"
        latlng = json.dumps([self.location[0], self.location[1]])
        lines = [f"var {var_name} = L.marker({latlng});"]
        if self.popup is not None:
            popup_js = json.dumps(str(self.popup))
            lines.append(f"{var_name}.bindPopup({popup_js});")
        if include_add:
            lines.append(f"{var_name}.addTo({map_var});")
        return var_name, "\n".join(lines)

    def add_to(self, parent):
        # If adding to a cluster, cluster aggregates markers
        if parent.__class__.__name__ == "MarkerCluster":
            parent.add_child(self)
            self._parent = parent
            return self
        return super().add_to(parent)


class CircleMarker(_Renderable):
    def __init__(self, location, radius=10, color="#3388ff", fill=True, fill_color=None, fill_opacity=0.2, name=None):
        self.location = tuple(location)
        self.radius = radius
        self.color = color
        self.fill = fill
        self.fill_color = fill_color or color
        self.fill_opacity = fill_opacity
        self.name = name or "CircleMarker"
        self._id = next(_id_counter)

    def render_js(self, map_var, include_add=True):
        var_name = f"circlemarker_{self._id}"
        latlng = json.dumps([self.location[0], self.location[1]])
        options = {
            "radius": int(self.radius),
            "color": self.color,
            "fill": bool(self.fill),
            "fillColor": self.fill_color,
            "fillOpacity": float(self.fill_opacity),
        }
        js = f"var {var_name} = L.circleMarker({latlng}, {json.dumps(options)}).addTo({map_var});"
        return var_name, js


class GeoJson(_Renderable):
    def __init__(self, data, name="GeoJson"):
        self.data = data
        self.name = name
        self._id = next(_id_counter)

    def _data_to_js(self):
        # If string, try to parse to ensure valid JSON; else embed as-is
        if isinstance(self.data, str):
            try:
                obj = json.loads(self.data)
                return json.dumps(obj)
            except Exception:
                # Assume it's raw JS/JSON snippet
                return self.data
        else:
            return json.dumps(self.data)

    def render_js(self, map_var, include_add=True):
        var_name = f"geojson_{self._id}"
        data_js = self._data_to_js()
        js = f"var {var_name} = L.geoJSON({data_js}).addTo({map_var});"
        return var_name, js


class LayerControl(_Renderable):
    def __init__(self):
        self._id = next(_id_counter)

    def render_js(self, map_var, include_add=True):
        # Map renders the control using collected layers
        return f"layercontrol_{self._id}", ""


# Backwards-compatible helper methods
def _chainable_add(obj, parent):
    parent.add_child(obj)
    return obj