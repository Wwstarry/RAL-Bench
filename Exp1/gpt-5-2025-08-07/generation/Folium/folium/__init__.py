# Minimal Folium-compatible public API surface implemented in pure Python.
# This package generates HTML+JS for Leaflet maps.

from .core import Map, Marker, CircleMarker, GeoJson, TileLayer, LayerControl

# Plugins anchor namespace
from . import plugins  # exposes plugins.MarkerCluster

__all__ = [
    "Map",
    "Marker",
    "CircleMarker",
    "GeoJson",
    "TileLayer",
    "LayerControl",
    "plugins",
]