"""
Functional tests for Map and basic layers.
"""

import folium
import json


def test_map_creation():
    """Test basic map creation."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    assert m.location == (45.5, -122.5)
    assert m.zoom_start == 12


def test_map_render():
    """Test map rendering to HTML."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    html = m.render()
    
    assert "<!DOCTYPE html>" in html
    assert "leaflet" in html.lower()
    assert "45.5" in html
    assert "-122.5" in html
    assert "12" in html


def test_map_with_marker():
    """Test map with marker."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    marker = folium.Marker(location=(45.5, -122.5), popup="Test Marker")
    m.add_child(marker)
    
    html = m.render()
    assert "L.marker" in html
    assert "Test Marker" in html


def test_map_with_circle_marker():
    """Test map with circle marker."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    circle = folium.CircleMarker(
        location=(45.5, -122.5),
        radius=10,
        color="red",
        popup="Circle"
    )
    m.add_child(circle)
    
    html = m.render()
    assert "L.circleMarker" in html
    assert "red" in html
    assert "Circle" in html


def test_map_with_geojson():
    """Test map with GeoJSON."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    
    geojson_data = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [-122.5, 45.5]
                },
                "properties": {"name": "Test Point"}
            }
        ]
    }
    
    geojson = folium.GeoJson(data=geojson_data)
    m.add_child(geojson)
    
    html = m.render()
    assert "L.geoJSON" in html
    assert "FeatureCollection" in html


def test_tile_layer():
    """Test tile layer."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12, tiles="CartoDB positron")
    html = m.render()
    
    assert "basemaps.cartocdn.com" in html
    assert "CartoDB" in html or "CARTO" in html


def test_layer_control():
    """Test layer control."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    control = folium.LayerControl()
    m.add_child(control)
    
    html = m.render()
    assert "L.control.layers" in html


def test_marker_with_tooltip():
    """Test marker with tooltip."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    marker = folium.Marker(
        location=(45.5, -122.5),
        popup="Popup Text",
        tooltip="Tooltip Text"
    )
    m.add_child(marker)
    
    html = m.render()
    assert "bindTooltip" in html
    assert "Tooltip Text" in html


def test_get_root():
    """Test get_root method."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    marker = folium.Marker(location=(45.5, -122.5))
    m.add_child(marker)
    
    assert marker.get_root() is m
    assert m.get_root() is m


def test_multiple_markers():
    """Test map with multiple markers."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    
    for i in range(5):
        marker = folium.Marker(
            location=(45.5 + i * 0.01, -122.5 + i * 0.01),
            popup=f"Marker {i}"
        )
        m.add_child(marker)
    
    html = m.render()
    assert html.count("L.marker") == 5
    for i in range(5):
        assert f"Marker {i}" in html


def test_circle_marker_styling():
    """Test circle marker with various styles."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    
    circle = folium.CircleMarker(
        location=(45.5, -122.5),
        radius=15,
        color="green",
        fillColor="yellow",
        fillOpacity=0.5,
        weight=3,
        opacity=0.8
    )
    m.add_child(circle)
    
    html = m.render()
    assert "green" in html
    assert "yellow" in html
    assert "0.5" in html
    assert "0.8" in html


def test_geojson_with_style():
    """Test GeoJSON with style options."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    
    geojson_data = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[-122.5, 45.5], [-122.4, 45.6]]
        }
    }
    
    geojson = folium.GeoJson(
        data=geojson_data,
        style={"color": "red", "weight": 5}
    )
    m.add_child(geojson)
    
    html = m.render()
    assert "L.geoJSON" in html
    assert "red" in html


def test_map_zoom_limits():
    """Test map zoom limits."""
    m = folium.Map(
        location=(45.5, -122.5),
        zoom_start=12,
        min_zoom=5,
        max_zoom=20
    )
    html = m.render()
    
    assert "minZoom" in html
    assert "maxZoom" in html
    assert "5" in html
    assert "20" in html