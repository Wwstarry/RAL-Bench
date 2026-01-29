import re

import folium
from folium.plugins import MarkerCluster


def test_map_root_render_contains_leaflet_assets_and_init():
    m = folium.Map(location=[0, 0], zoom_start=2)
    html = m.get_root().render()
    assert "<!DOCTYPE html>" in html
    assert "leaflet.css" in html
    assert "leaflet.js" in html
    assert "L.map(" in html
    assert re.search(r'<div id="map_[^"]+"></div>', html)


def test_marker_and_circlemarker_render_popup_tooltip():
    m = folium.Map(location=[1, 2], zoom_start=3)
    folium.Marker([1, 2], popup='Hello "world"', tooltip="Tip").add_to(m)
    folium.CircleMarker([3, 4], radius=7, popup="C").add_to(m)
    html = m.get_root().render()
    assert "L.marker([1.0,2.0]" in html or "L.marker([1,2]" in html
    assert "bindPopup(" in html
    assert '\\"world\\"' in html or '"world"' in html  # JSON escaping present
    assert "bindTooltip(" in html
    assert "L.circleMarker(" in html
    assert '"radius":7' in html or "radius" in html


def test_tilelayer_and_layercontrol_show_false_not_added():
    m = folium.Map(location=[0, 0], zoom_start=2, tiles=None)
    tl1 = folium.TileLayer("OpenStreetMap", name="OSM", overlay=False, control=True, show=True).add_to(m)
    tl2 = folium.TileLayer(
        "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        name="Custom",
        overlay=False,
        control=True,
        show=False,
    ).add_to(m)
    folium.LayerControl().add_to(m)
    html = m.get_root().render()

    assert "L.control.layers" in html
    assert '"OSM"' in html
    assert '"Custom"' in html
    # Custom is show=False so it shouldn't be added to map automatically
    assert f"{tl2.get_name()}.addTo(" not in html
    # OSM show=True should be added
    assert f"{tl1.get_name()}.addTo(" in html


def test_geojson_basic_and_style_constant():
    geo = {
        "type": "FeatureCollection",
        "features": [
            {"type": "Feature", "properties": {"x": 1}, "geometry": {"type": "Point", "coordinates": [10, 20]}},
        ],
    }
    m = folium.Map(location=[0, 0], zoom_start=2, tiles=None)
    gj = folium.GeoJson(geo, name="geo", style_function={"color": "red"}, show=True).add_to(m)
    folium.LayerControl().add_to(m)
    html = m.get_root().render()
    assert "L.geoJSON" in html
    assert "[10,20]" in html or "[10.0,20.0]" in html
    assert '"color":"red"' in html
    assert '"geo"' in html
    assert gj.get_name() in html


def test_markercluster_assets_and_marker_targeting_and_single_in_control():
    m = folium.Map(location=[0, 0], zoom_start=2, tiles=None)
    mc = MarkerCluster(name="Cluster").add_to(m)
    for i in range(50):
        folium.Marker([i * 0.01, i * 0.01]).add_to(mc)
    folium.LayerControl().add_to(m)
    html = m.get_root().render()

    assert "leaflet.markercluster.js" in html
    assert "MarkerCluster.css" in html
    assert "L.markerClusterGroup" in html

    # Markers should add to cluster, not map directly (at least predominantly)
    assert f".addTo({mc.get_name()})" in html
    assert f".addTo({m.get_name()})" not in html or html.count(f".addTo({m.get_name()})") < 10

    # Cluster should appear as a single overlay in layer control
    assert '"Cluster"' in html


def test_markercluster_assets_included_once_for_two_clusters():
    m = folium.Map(location=[0, 0], zoom_start=2, tiles=None)
    mc1 = MarkerCluster().add_to(m)
    mc2 = MarkerCluster().add_to(m)
    folium.Marker([0, 0]).add_to(mc1)
    folium.Marker([1, 1]).add_to(mc2)
    html = m.get_root().render()

    assert html.count("leaflet.markercluster.js") == 1
    assert html.count("MarkerCluster.css") == 1
    assert html.count("MarkerCluster.Default.css") == 1


def test_cluster_reduces_direct_addto_map_occurrences():
    m1 = folium.Map(location=[0, 0], zoom_start=2, tiles=None)
    for i in range(200):
        folium.Marker([i * 0.001, i * 0.001]).add_to(m1)
    html1 = m1.get_root().render()

    m2 = folium.Map(location=[0, 0], zoom_start=2, tiles=None)
    mc = MarkerCluster().add_to(m2)
    for i in range(200):
        folium.Marker([i * 0.001, i * 0.001]).add_to(mc)
    html2 = m2.get_root().render()

    # Direct version should have many addTo(map)
    c1 = html1.count(f".addTo({m1.get_name()})")
    # Cluster version should have far fewer direct addTo(map) calls (ideally 1 for the cluster)
    c2 = html2.count(f".addTo({m2.get_name()})")
    assert c1 > 100
    assert c2 < 10