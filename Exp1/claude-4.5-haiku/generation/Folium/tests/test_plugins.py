"""
Tests for Folium plugins.
"""

import folium
from folium.plugins import MarkerCluster


def test_marker_cluster_creation():
    """Test MarkerCluster creation."""
    cluster = MarkerCluster()
    assert cluster is not None


def test_marker_cluster_with_markers():
    """Test MarkerCluster with markers."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    cluster = MarkerCluster()
    
    for i in range(10):
        marker = folium.Marker(
            location=(45.5 + i * 0.01, -122.5 + i * 0.01),
            popup=f"Marker {i}"
        )
        cluster.add_child(marker)
    
    m.add_child(cluster)
    html = m.render()
    
    assert "markerClusterGroup" in html
    assert "leaflet.markercluster" in html


def test_marker_cluster_options():
    """Test MarkerCluster with options."""
    cluster = MarkerCluster(options={"maxClusterRadius": 50})
    
    for i in range(5):
        marker = folium.Marker(location=(45.5 + i * 0.01, -122.5 + i * 0.01))
        cluster.add_child(marker)
    
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    m.add_child(cluster)
    html = m.render()
    
    assert "maxClusterRadius" in html
    assert "50" in html


def test_marker_cluster_large_dataset():
    """Test MarkerCluster with large number of markers."""
    m = folium.Map(location=(45.5, -122.5), zoom_start=12)
    cluster = MarkerCluster()
    
    # Add 100 markers
    for i in range(100):
        lat = 45.5 + (i % 10) * 0.01
        lon = -122.5 + (i // 10) * 0.01
        marker = folium.Marker(location=(lat, lon))
        cluster.add_child(marker)
    
    m.add_child(cluster)
    html = m.render()
    
    # Verify clustering is used (should reduce output size compared to 100 individual markers)
    assert "markerClusterGroup" in html
    assert len(html) < 500000  # Should be reasonably sized