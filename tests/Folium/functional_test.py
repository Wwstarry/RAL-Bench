import importlib
import os
import sys
from pathlib import Path


TARGET_ENV = "FOLIUM_TARGET"
TARGET_REFERENCE_VALUE = "reference"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_repo_root() -> Path:
    env_root = os.getenv("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return (_project_root() / "repositories" / "folium").resolve()


def _prepend_import_path():
    repo = _resolve_repo_root()
    sys.path.insert(0, str(repo))


def _plugins_module():
    # Folium does not guarantee `folium.plugins` attribute on top-level module.
    return importlib.import_module("folium.plugins")


def test_000_sanity_print_test_file_path():
    # Prevent “running stale tests” issues.
    print(f"RUNNING_TEST_FILE={Path(__file__).resolve()}")


def test_001_import_folium():
    _prepend_import_path()
    import folium  # noqa: F401


def test_002_create_basic_map_renders_leaflet():
    _prepend_import_path()
    import folium

    m = folium.Map(location=[0, 0], zoom_start=2)
    html = m.get_root().render()
    assert "leaflet" in html.lower()


def test_003_map_has_html_root():
    _prepend_import_path()
    import folium

    m = folium.Map(location=[0, 0], zoom_start=2)
    root = m.get_root()
    assert hasattr(root, "render")
    html = root.render().lower()
    assert "<html" in html


def test_004_add_marker_layer_changes_output():
    _prepend_import_path()
    import folium

    m = folium.Map(location=[0, 0], zoom_start=2)
    base = m.get_root().render()

    folium.Marker([0, 0], tooltip="t").add_to(m)
    html = m.get_root().render()
    assert len(html) > len(base)
    assert "marker" in html.lower()


def test_005_add_circle_marker_changes_output():
    _prepend_import_path()
    import folium

    m = folium.Map(location=[0, 0], zoom_start=2)
    base = m.get_root().render()

    folium.CircleMarker([0, 0], radius=5).add_to(m)
    html = m.get_root().render()
    assert len(html) > len(base)


def test_006_add_tile_layer_and_layer_control():
    _prepend_import_path()
    import folium

    m = folium.Map(location=[0, 0], zoom_start=2, tiles=None)
    folium.TileLayer("OpenStreetMap", name="osm").add_to(m)
    folium.LayerControl().add_to(m)

    html = m.get_root().render().lower()
    assert "layercontrol" in html or "layers" in html


def test_007_geojson_adds_feature_collection():
    _prepend_import_path()
    import folium

    gj = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "p"},
                "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
            }
        ],
    }

    m = folium.Map(location=[0, 0], zoom_start=2)
    folium.GeoJson(gj, name="g").add_to(m)

    html = m.get_root().render().lower()
    assert "featurecollection" in html or "geojson" in html


def test_008_geojson_style_function_serializes():
    _prepend_import_path()
    import folium

    gj = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"style": "x"},
                "geometry": {"type": "Point", "coordinates": [0.0, 0.0]},
            }
        ],
    }

    def style_fn(feature):
        _ = feature
        return {"color": "red", "weight": 2}

    m = folium.Map(location=[0, 0], zoom_start=2)
    folium.GeoJson(gj, style_function=style_fn).add_to(m)

    html = m.get_root().render().lower()
    assert "color" in html or "weight" in html


def test_009_map_save_writes_html(tmp_path: Path):
    _prepend_import_path()
    import folium

    out = tmp_path / "m.html"
    m = folium.Map(location=[0, 0], zoom_start=2)
    m.save(str(out))

    assert out.exists()
    txt = out.read_text(encoding="utf-8", errors="ignore").lower()
    assert "<html" in txt


def test_010_plugins_markercluster_module_importable():
    _prepend_import_path()
    plugins = _plugins_module()
    assert hasattr(plugins, "MarkerCluster"), "Expected MarkerCluster in folium.plugins"


def test_011_markercluster_adds_cluster_snippet():
    _prepend_import_path()
    import folium

    plugins = _plugins_module()
    MarkerCluster = getattr(plugins, "MarkerCluster")

    m = folium.Map(location=[0, 0], zoom_start=2)
    mc = MarkerCluster(name="mc").add_to(m)
    assert mc is not None

    html = m.get_root().render().lower()
    assert "markercluster" in html or "cluster" in html
