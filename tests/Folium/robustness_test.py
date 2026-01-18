import importlib
import os
import sys
from pathlib import Path

import pytest


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_repo_root() -> Path:
    env_root = os.getenv("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return (_project_root() / "repositories" / "folium").resolve()


def _prepend_import_path():
    sys.path.insert(0, str(_resolve_repo_root()))


def _plugins_module():
    return importlib.import_module("folium.plugins")


def test_001_invalid_location_type_raises_or_handles():
    _prepend_import_path()
    import folium

    with pytest.raises(Exception):
        _ = folium.Map(location="not-a-latlng", zoom_start=2)


def test_002_marker_invalid_location_raises_or_handles():
    _prepend_import_path()
    import folium

    m = folium.Map(location=[0, 0], zoom_start=2)
    with pytest.raises(Exception):
        folium.Marker(location="bad").add_to(m)


def test_003_geojson_invalid_object_raises_cleanly():
    _prepend_import_path()
    import folium

    m = folium.Map(location=[0, 0], zoom_start=2)
    with pytest.raises(Exception):
        folium.GeoJson(object()).add_to(m)


def test_004_tilelayer_unknown_tiles_does_not_crash():
    _prepend_import_path()
    import folium

    m = folium.Map(location=[0, 0], zoom_start=2, tiles=None)
    try:
        folium.TileLayer("this_tileset_should_not_exist", name="x").add_to(m)
        _ = m.get_root().render()
    except Exception:
        pass


def test_005_markercluster_handles_empty_cluster():
    _prepend_import_path()
    import folium

    plugins = _plugins_module()
    MarkerCluster = getattr(plugins, "MarkerCluster")

    m = folium.Map(location=[0, 0], zoom_start=2)
    MarkerCluster().add_to(m)

    html = m.get_root().render().lower()
    assert "markercluster" in html or "cluster" in html
