"""
Minimal implementation of the :pymod:`folium.plugins` namespace.

Only the *MarkerCluster* plugin is available.
"""
from importlib import import_module as _imp

# Re-export for convenience
_marker_cluster = _imp("folium.plugins.marker_cluster")
MarkerCluster = _marker_cluster.MarkerCluster

__all__ = ["MarkerCluster"]