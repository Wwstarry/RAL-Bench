import json
from .core import _id_counter

class MarkerCluster:
    """
    Minimal MarkerCluster plugin compatibility:
    - Acts as a container for many Marker objects.
    - Renders a single cluster layer and aggregates markers in JS loops.
    """
    def __init__(self, name="MarkerCluster"):
        self.name = name
        self._id = next(_id_counter)
        self._children = []
        # Flag for Map to include plugin assets
        self._sets_markercluster = True

    def add_child(self, child):
        # Child is expected to be a Marker
        self._children.append(child)
        child._parent = self
        return self

    def add_to(self, parent):
        # attach to Map
        parent.add_child(self)
        self._parent = parent
        return self

    def render_js(self, map_var, include_add=True):
        var_name = f"markercluster_{self._id}"
        lines = [f"var {var_name} = L.markerClusterGroup();"]
        # Aggregate marker data into a JS array to minimize output size
        data = []
        for m in self._children:
            lat, lng = m.location
            record = [lat, lng]
            if m.popup is not None:
                record.append(str(m.popup))
            data.append(record)
        # Serialize as JSON; keep popups as strings
        data_js = json.dumps(data)
        lines.append(f"var {var_name}_data = {data_js};")
        lines.append(f"{var_name}_data.forEach(function(d) {{ var m = L.marker([d[0], d[1]]); if (d.length > 2) {{ m.bindPopup(String(d[2])); }} {var_name}.addLayer(m); }});")
        if include_add:
            lines.append(f"{var_name}.addTo({map_var});")
        return var_name, "\n".join(lines)