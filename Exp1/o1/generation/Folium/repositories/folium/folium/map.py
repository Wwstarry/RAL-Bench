"""
Implementation of the Map object and HTML rendering.
"""

import json

class Map:
    def __init__(self, location=None, zoom_start=13, width="100%", height="100%", **kwargs):
        self.location = location or [0, 0]
        self.zoom_start = zoom_start
        self.width = width
        self.height = height
        self._children = []
        self._name = "Map"
        # Keep track whether a marker cluster plugin is used
        self._has_marker_cluster = False

    def add_child(self, child):
        self._children.append(child)
        child._parent = self
        if getattr(child, "_is_marker_cluster_plugin", False):
            self._has_marker_cluster = True

    def add_to(self, parent):
        parent.add_child(self)

    def get_root(self):
        """
        Compatible with Folium's .get_root() usage.
        For simplicity, we return self.
        """
        return self

    def render(self):
        """
        Produce an HTML string containing Leaflet map + children.
        """
        children_scripts = []
        children_elements = []

        for child in self._children:
            script, element = child.render()
            if script:
                children_scripts.append(script)
            if element:
                children_elements.append(element)

        # Basic Leaflet includes
        leaflet_css = "https://unpkg.com/leaflet@1.7.1/dist/leaflet.css"
        leaflet_js = "https://unpkg.com/leaflet@1.7.1/dist/leaflet.js"

        # Marker cluster plugin includes, if needed
        cluster_css = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/MarkerCluster.css"
        cluster_js = "https://unpkg.com/leaflet.markercluster@1.5.3/dist/leaflet.markercluster.js"

        map_div_id = "mapid"

        # Map initialization script
        init_script = f"""
            var map = L.map('{map_div_id}').setView([{self.location[0]}, {self.location[1]}], {self.zoom_start});
        """

        html_template = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <style>
        #{map_div_id} {{
            width: {self.width};
            height: {self.height};
        }}
    </style>
    <link rel="stylesheet" href="{leaflet_css}" />
    <script src="{leaflet_js}"></script>
    {f'<link rel="stylesheet" href="{cluster_css}" />' if self._has_marker_cluster else ""}
    {f'<script src="{cluster_js}"></script>' if self._has_marker_cluster else ""}
</head>
<body>
    <div id="{map_div_id}"></div>
    <script>
    {init_script}
    {''.join(children_scripts)}
    </script>
    {''.join(children_elements)}
</body>
</html>
        """
        return html_template