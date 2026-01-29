import folium

def test_map_render_contains_leaflet():
    m = folium.Map(location=[45.5236, -122.6750], zoom_start=13)
    html = m.get_root().render()
    assert 'leaflet.js' in html
    assert 'L.map(' in html
    assert 'OpenStreetMap' in html

def test_marker_addition():
    m = folium.Map(location=[0, 0])
    folium.Marker([0, 0], popup="Hello").add_to(m)
    html = m.get_root().render()
    assert 'L.marker' in html
    assert 'Hello' in html

def test_circlemarker():
    m = folium.Map(location=[0, 0])
    folium.CircleMarker([0, 0], radius=20, color='red').add_to(m)
    html = m.get_root().render()
    assert 'L.circleMarker' in html
    assert 'red' in html

def test_geojson():
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature",
             "geometry": {"type": "Point", "coordinates": [0, 0]},
             "properties": {"name": "Null Island"}
            }
        ]
    }
    m = folium.Map(location=[0, 0])
    folium.GeoJson(geojson).add_to(m)
    html = m.get_root().render()
    assert 'L.geoJSON' in html
    assert 'Null Island' in html

def test_tilelayer():
    m = folium.Map(location=[0, 0], tiles=None)
    folium.TileLayer('Stamen Terrain').add_to(m)
    html = m.get_root().render()
    assert 'Stamen Design' in html

def test_layercontrol():
    m = folium.Map(location=[0, 0])
    folium.LayerControl().add_to(m)
    html = m.get_root().render()
    assert 'L.control.layers' in html

def test_markercluster():
    m = folium.Map(location=[0, 0])
    from folium.plugins import MarkerCluster
    cluster = MarkerCluster()
    for i in range(10):
        folium.Marker([i, i], popup=f"Marker {i}").add_to(cluster)
    cluster.add_to(m)
    html = m.get_root().render()
    assert 'markerClusterGroup' in html
    assert 'leaflet.markercluster.js' in html
    assert 'Marker 0' in html
    assert 'Marker 9' in html