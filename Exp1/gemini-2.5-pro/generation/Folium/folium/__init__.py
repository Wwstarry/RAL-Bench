"""
folium
------

Make beautiful maps with Python and Leaflet.js

"""

from .map import Map
from .features import (
    Marker,
    CircleMarker,
    GeoJson,
    TileLayer,
    LayerControl,
)
from . import plugins

__version__ = "0.1.0"

__all__ = [
    "__version__",
    "Map",
    "Marker",
    "CircleMarker",
    "GeoJson",
    "TileLayer",
    "LayerControl",
    "plugins",
]