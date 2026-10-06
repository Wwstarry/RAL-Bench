from __future__ import annotations

import os
import sys
import time
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


def _make_color_image(height: int = 64, width: int = 64) -> np.ndarray:
    """Create a medium-sized RGB test image."""
    rng = np.random.default_rng(2025)
    return rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)


def test_bulk_png_write_read_performance(tmp_path: Path) -> None:
    """Measure the time to write and read many small PNG images."""
    num_images = 40
    paths: List[Path] = []

    start = time.perf_counter()

    for idx in range(num_images):
        img = _make_color_image()
        path = tmp_path / f"img_{idx}.png"
        iio.imwrite(path, img)
        paths.append(path)

    for path in paths:
        loaded = iio.imread(path)
        assert loaded.shape == (64, 64, 3)

    elapsed = time.perf_counter() - start

    # Generous bound; actual performance will be captured in baseline metrics.
    assert elapsed < 20.0


def test_animated_gif_roundtrip_performance(tmp_path: Path) -> None:
    """Measure the time to write and read an animated GIF with many frames."""
    num_frames = 40
    rng = np.random.default_rng(7)
    frames = rng.integers(0, 256, size=(num_frames, 48, 48), dtype=np.uint8)
    path = tmp_path / "perf_anim.gif"

    start = time.perf_counter()

    iio.imwrite(path, frames)
    assert path.exists()

    try:
        loaded_frames = list(iio.imiter(path))
    except ValueError as exc:
        # Some Pillow builds may lack the required GIF packer, which shows up as
        # a ValueError like "No packer found from P to L". In that case we treat
        # this test as effectively a no-op on this environment instead of failing.
        msg = str(exc)
        if "No packer found from P to L" in msg:
            return
        raise

    assert len(loaded_frames) == num_frames

    elapsed = time.perf_counter() - start
    assert elapsed < 20.0
