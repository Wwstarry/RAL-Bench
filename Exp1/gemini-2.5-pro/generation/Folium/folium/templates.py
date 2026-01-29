"""
Templates for Folium.
"""

LEAFLET_JS = "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.js"
LEAFLET_CSS = "https://cdn.jsdelivr.net/npm/leaflet@1.9.3/dist/leaflet.css"

JS_LINK = '<script src="{url}"></script>'
CSS_LINK = '<link rel="stylesheet" href="{url}"/>'

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <style>
        html, body {{
            width: 100%;
            height: 100%;
            margin: 0;
            padding: 0;
        }}
        #{map_id} {{
            position: absolute;
            top: 0;
            bottom: 0;
            right: 0;
            left: 0;
        }}
    </style>
    {header}
</head>
<body>
    <div id="{map_id}"></div>
    <script>
        var {map_variable} = L.map('{map_id}', {{
            center: {location},
            zoom: {zoom_start},
            crs: L.CRS.EPSG3857,
            zoomControl: true,
            preferCanvas: false,
        }});
        {script}
    </script>
</body>
</html>
"""