from __future__ import annotations

import os
import sys
import tracemalloc
from pathlib import Path
from typing import List

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]

TARGET_ENV = os.getenv("IMAGEIO_TARGET", "reference")
if TARGET_ENV == "reference":
    REPO_ROOT = ROOT / "repositories" / "Imageio"
elif TARGET_ENV == "generation":
    REPO_ROOT = ROOT / "generation" / "Imageio"
else:
    raise RuntimeError(f"Unsupported IMAGEIO_TARGET value: {TARGET_ENV}")

if not REPO_ROOT.exists():
    raise RuntimeError(f"Repository root does not exist: {REPO_ROOT}")

if (REPO_ROOT / "imageio").exists():
    PACKAGE_ROOT = REPO_ROOT
else:
    raise RuntimeError(f"Could not find 'imageio' package directory under {REPO_ROOT}")

sys.path.insert(0, str(PACKAGE_ROOT))

import imageio.v3 as iio  # type: ignore[import]


def _png_io_workload(tmp_path: Path, loops: int = 80) -> None:
    """Perform repeated PNG write/read operations to exercise memory usage."""
    path = tmp_path / "resource_png.png"
    rng = np.random.default_rng(42)
    img = rng.integers(0, 256, size=(64, 64, 3), dtype=np.uint8)

    for _ in range(loops):
        iio.imwrite(path, img)
        _ = iio.imread(path)


def _gif_iter_workload(tmp_path: Path, loops: int = 30) -> None:
    """Perform repeated GIF writes and frame iteration to exercise memory usage."""
    num_frames = 10
    rng = np.random.default_rng(99)
    frames = rng.integers(0, 256, size=(num_frames, 32, 32), dtype=np.uint8)
    path = tmp_path / "resource_anim.gif"

    for _ in range(loops):
        iio.imwrite(path, frames)
        frames_read = list(iio.imiter(path))
        assert len(frames_read) == num_frames


def test_memory_usage_under_repeated_png_io(tmp_path: Path) -> None:
    """Ensure repeated PNG roundtrips stay within a coarse memory bound."""
    tracemalloc.start()

    _png_io_workload(tmp_path)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    max_allowed_bytes = 200 * 1024 * 1024
    assert peak < max_allowed_bytes


def test_memory_usage_under_animated_gif_io(tmp_path: Path) -> None:
    """Ensure repeated animated GIF IO does not cause unbounded memory growth."""
    tracemalloc.start()

    _gif_iter_workload(tmp_path)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    max_allowed_bytes = 200 * 1024 * 1024
    assert peak < max_allowed_bytes
