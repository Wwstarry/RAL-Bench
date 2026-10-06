import importlib
import os
import sys
import time
from pathlib import Path


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


def test_performance_large_marker_map_build_and_html_size():
    _prepend_import_path()
    import folium

    n = 2000

    t0 = time.perf_counter()
    m = folium.Map(location=[0, 0], zoom_start=2)
    for i in range(n):
        folium.Marker([i * 1e-6, i * 1e-6]).add_to(m)
    html = m.get_root().render()
    t1 = time.perf_counter()

    print(
        f"PERF_FOLIUM plain_markers={n} "
        f"build_time_s={t1 - t0:.6f} "
        f"html_bytes={len(html.encode('utf-8', 'ignore'))}"
    )


def test_performance_markercluster_build_and_html_size():
    _prepend_import_path()
    import folium

    plugins = _plugins_module()
    MarkerCluster = getattr(plugins, "MarkerCluster")

    n = 2000

    t0 = time.perf_counter()
    m = folium.Map(location=[0, 0], zoom_start=2)
    mc = MarkerCluster(name="mc").add_to(m)
    for i in range(n):
        folium.Marker([i * 1e-6, i * 1e-6]).add_to(mc)
    html = m.get_root().render()
    t1 = time.perf_counter()

    print(
        f"PERF_FOLIUM markercluster_markers={n} "
        f"build_time_s={t1 - t0:.6f} "
        f"html_bytes={len(html.encode('utf-8', 'ignore'))}"
    )
