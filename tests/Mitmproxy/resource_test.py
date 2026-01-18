import os
import sys
from pathlib import Path

import psutil


TARGET_ENV = "MITMPROXY_TARGET"
TARGET_REFERENCE_VALUE = "reference"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _repo_root() -> Path:
    env_root = os.getenv("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return (_project_root() / "repositories" / "mitmproxy").resolve()


def _pythonpath_root() -> Path:
    repo = _repo_root()
    if (repo / "src" / "mitmproxy").is_dir():
        return (repo / "src").resolve()
    return repo.resolve()


def test_resource_import_mitmproxy_rss_delta():
    """
    Resource sampling around a stable workload:
    - import mitmproxy (top-level only)
    """
    sys.path.insert(0, str(_pythonpath_root()))
    proc = psutil.Process()
    rss_before = proc.memory_info().rss

    import mitmproxy  # noqa: F401

    rss_after = proc.memory_info().rss
    rss_delta = rss_after - rss_before

    print(f"METRIC resource.import_mitmproxy.rss_before_bytes={rss_before}")
    print(f"METRIC resource.import_mitmproxy.rss_after_bytes={rss_after}")
    print(f"METRIC resource.import_mitmproxy.rss_delta_bytes={rss_delta}")
