import os
import sys
import time
import subprocess
from pathlib import Path


TARGET_ENV = "SQLMAP_TARGET"
TARGET_REFERENCE_VALUE = "reference"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _repo_root() -> Path:
    env_root = os.getenv("RACB_REPO_ROOT")
    if env_root:
        return Path(env_root).resolve()
    return (_project_root() / "repositories" / "sqlmap").resolve()


def _entrypoint() -> Path:
    return (_repo_root() / "sqlmap.py").resolve()


def test_performance_help_startup_time():
    """
    Measure CLI startup/argument parsing cost via a benign invocation (-h).
    No hard threshold; emit a METRIC line for the runner.
    """
    cmd = [sys.executable, str(_entrypoint()), "-h"]

    t0 = time.perf_counter()
    p = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
        cwd=str(_repo_root()),
        env={**os.environ},
    )
    t1 = time.perf_counter()

    assert p.returncode == 0
    elapsed_s = t1 - t0
    print(f"METRIC performance.help_startup.elapsed_s={elapsed_s:.6f}")
