import os
import sys
import time
import subprocess
from pathlib import Path

import psutil


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


def test_resource_help_invocation_rss_delta():
    """
    Sample RSS around a benign help invocation (-h).
    Mirrors the Astral resource_test style: psutil rss before/after.
    """
    proc = psutil.Process()
    rss_before = proc.memory_info().rss

    t0 = time.perf_counter()
    p = subprocess.run(
        [sys.executable, str(_entrypoint()), "-h"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
        cwd=str(_repo_root()),
        env={**os.environ},
    )
    t1 = time.perf_counter()

    rss_after = proc.memory_info().rss
    rss_delta = rss_after - rss_before
    elapsed_s = t1 - t0

    assert p.returncode == 0

    print(f"METRIC resource.help.elapsed_s={elapsed_s:.6f}")
    print(f"METRIC resource.help.rss_before_bytes={rss_before}")
    print(f"METRIC resource.help.rss_after_bytes={rss_after}")
    print(f"METRIC resource.help.rss_delta_bytes={rss_delta}")
