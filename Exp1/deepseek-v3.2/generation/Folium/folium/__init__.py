"""
Folium - A Python library for interactive maps using Leaflet.js
"""

from folium.map import Map
from folium.features import (
    Marker,
    CircleMarker,
    GeoJson,
    TileLayer,
    LayerControl,
)

__version__ = "0.1.0"
__all__ = [
    "Map",
    "Marker",
    "CircleMarker",
    "GeoJson",
    "TileLayer",
    "LayerControl",
]

# Plugins namespace
class plugins:
    """Plugins namespace for folium extensions"""
    pass