"""
Performance tests for Folium.
"""

import folium
from folium.plugins import MarkerCluster
import time


def test_map_render_time_small():
    """Test render time for small map."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    
    for i in range(10):
        marker = folium.Marker(location=(45.5 + i * 0.01, -122.5 + i * 0.01))
        m.add_child(marker)
    
    start = time.time()
    html = m.render()
    elapsed = time.time() - start
    
    assert elapsed < 1.0  # Should render in under 1 second
    assert len(html) > 1000  # Should produce meaningful HTML


def test_map_render_time_medium():
    """Test render time for medium map."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    
    for i in range(100):
        lat = 45.5 + (i % 10) * 0.01
        lon = -122.5 + (i // 10) * 0.01
        marker = folium.Marker(location=(lat, lon))
        m.add_child(marker)
    
    start = time.time()
    html = m.render()
    elapsed = time.time() - start
    
    assert elapsed < 5.0  # Should render in under 5 seconds
    assert len(html) > 10000


def test_marker_cluster_performance():
    """Test that clustering improves performance for large datasets."""
    # Create map with clustered markers
    m_clustered = folium.Map(location=(45.5, -122.5), zoom_start=12)
    cluster = MarkerCluster()
    
    for i in range(200):
        lat = 45.5 + (i % 20) * 0.005
        lon = -122.5 + (i // 20) * 0.005
        marker = folium.Marker(location=(lat, lon))
        cluster.add_child(marker)
    
    m_clustered.add_child(cluster)
    
    start = time.time()
    html_clustered = m_clustered.render()
    time_clustered = time.time() - start
    
    # Create map without clustering
    m_unclustered = folium.Map(location=(45.5, -122.5), zoom_start=12)
    
    for i in range(200):
        lat = 45.5 + (i % 20) * 0.005
        lon = -122.5 + (i // 20) * 0.005
        marker = folium.Marker(location=(lat, lon))
        m_unclustered.add_child(marker)
    
    start = time.time()
    html_unclustered = m_unclustered.render()
    time_unclustered = time.time() - start
    
    # Clustered version should be faster and produce smaller HTML
    assert time_clustered < time_unclustered * 1.5  # Allow some overhead
    assert len(html_clustered) < len(html_unclustered)


def test_html_size_scales_reasonably():
    """Test that HTML size scales reasonably with marker count."""
    sizes = []
    
    for count in [10, 50, 100]:
        m = folium.Map(location=(45.5, -122.5), zoom_start=12)
        
        for i in range(count):
            lat = 45.5 + (i % 10) * 0.01
            lon = -122.5 + (i // 10) * 0.01
            marker = folium.Marker(location=(lat, lon))
            m.add_child(marker)
        
        html = m.render()
        sizes.append(len(html))
    
    # HTML size should grow roughly linearly with marker count
    # (not exponentially)
    ratio_1 = sizes[1] / sizes[0]  # 50 markers / 10 markers
    ratio_2 = sizes[2] / sizes[1]  # 100 markers / 50 markers
    
    # Both ratios should be in reasonable range (between 2 and 10)
    assert 2 < ratio_1 < 10
    assert 2 < ratio_2 < 10


def test_geojson_render_performance():
    """Test GeoJSON rendering performance."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    
    # Create a GeoJSON with multiple features
    features = []
    for i in range(50):
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [-122.5 + i * 0.01, 45.5 + i * 0.01]
            },
            "properties": {"id": i}
        })
    
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    
    geojson = folium.GeoJson(data=geojson_data)
    m.add_child(geojson)
    
    start = time.time()
    html = m.render()
    elapsed = time.time() - start
    
    assert elapsed < 2.0  # Should render quickly
    assert "FeatureCollection" in html