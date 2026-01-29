"""
A lightweight, pure-Python subset of Folium compatible with key APIs used in tests.

This library generates HTML/JS using Leaflet.js concepts and supports a small set of
core objects: Map, Marker, CircleMarker, GeoJson, TileLayer, LayerControl, and a
plugins anchor with MarkerCluster.

Design goals:
- Simple composition: map.add_child(layer) or layer.add_to(map)
- map.get_root().render() -> full HTML document
- Reasonable output size; MarkerCluster compresses large marker sets
"""

from .map import Map
from .features import Marker, CircleMarker, GeoJson, TileLayer, LayerControl
from . import plugins

__all__ = [
    "Map",
    "Marker",
    "CircleMarker",
    "GeoJson",
    "TileLayer",
    "LayerControl",
    "plugins",
]