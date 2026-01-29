"""
Folium: Python library for generating interactive maps with Leaflet.js
"""

__version__ = "0.14.0"

from folium.map import Map, Marker, CircleMarker, GeoJson, TileLayer, LayerControl
from folium import plugins

__all__ = [
    "Map",
    "Marker",
    "CircleMarker",
    "GeoJson",
    "TileLayer",
    "LayerControl",
    "plugins",
]