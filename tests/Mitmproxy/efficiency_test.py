import os
import sys
import time
import subprocess
from pathlib import Path


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


def test_performance_import_mitmproxy_elapsed():
    """
    Measure a stable, dependency-light workload:
    - import mitmproxy (top-level)
    This avoids importing CLI stack that may require mitmproxy_rs/OpenSSL.
    """
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["PYTHONPATH"] = str(_pythonpath_root()) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")

    code = "import mitmproxy; print('ok')"
    t0 = time.perf_counter()
    p = subprocess.run(
        [sys.executable, "-c", code],
        text=True,
        capture_output=True,
        timeout=30,
        env=env,
    )
    t1 = time.perf_counter()

    assert p.returncode == 0
    elapsed_s = t1 - t0
    print(f"METRIC performance.import_mitmproxy.elapsed_s={elapsed_s:.6f}")
