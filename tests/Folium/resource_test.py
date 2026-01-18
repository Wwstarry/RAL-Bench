import os
import sys
from pathlib import Path

import psutil

TARGET_ENV = "FOLIUM_TARGET"
TARGET_REFERENCE_VALUE = "reference"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _resolve_repo_root() -> Path:
    root = _project_root()
    target = os.getenv(TARGET_ENV, TARGET_REFERENCE_VALUE)
    if target == TARGET_REFERENCE_VALUE:
        rr = os.getenv("RACB_REPO_ROOT")
        repo = Path(rr).resolve() if rr else (root / "repositories" / "folium").resolve()
    else:
        repo = (root / "generation" / "Folium").resolve()

    if (repo / "src" / "folium").is_dir():
        return (repo / "src").resolve()
    return repo.resolve()


def test_resource_build_medium_map_rss_cpu():
    sys.path.insert(0, str(_resolve_repo_root()))
    import folium

    proc = psutil.Process()
    rss_before = proc.memory_info().rss
    _ = proc.cpu_percent(interval=None)

    m = folium.Map(location=[0, 0], zoom_start=2)
    for i in range(500):
        folium.CircleMarker([0 + i * 1e-3, 0 + i * 1e-3], radius=3).add_to(m)
    _ = m.get_root().render()

    cpu = proc.cpu_percent(interval=0.2)
    rss_after = proc.memory_info().rss

    print(f"METRIC resource.medium_map.rss_before_bytes={rss_before}")
    print(f"METRIC resource.medium_map.rss_after_bytes={rss_after}")
    print(f"METRIC resource.medium_map.cpu_percent_sample={cpu:.2f}")

    assert rss_after >= 0
    assert cpu >= 0.0
