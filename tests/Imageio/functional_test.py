from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# Repo root resolution (RACB-compatible + local fallback)
#
# RACB requirement: prefer RACB_REPO_ROOT and support both layouts:
#   - <repo_root>/imageio/__init__.py
#   - <repo_root>/src/imageio/__init__.py
#
# Local fallback (no absolute path hardcode): use this eval repo layout:
#   <eval_root>/repositories/Imageio   OR   <eval_root>/generation/Imageio
# ---------------------------------------------------------------------------

PACKAGE_NAME = "imageio"

_racb_root = os.environ.get("RACB_REPO_ROOT", "").strip()
if _racb_root:
    REPO_ROOT = Path(_racb_root).resolve()
else:
    ROOT = Path(__file__).resolve().parents[2]
    target = os.getenv("IMAGEIO_TARGET", "reference").lower()
    if target == "reference":
        REPO_ROOT = ROOT / "repositories" / "Imageio"
    elif target == "generation":
        REPO_ROOT = ROOT / "generation" / "Imageio"
    else:
        pytest.skip(
            "Unsupported IMAGEIO_TARGET value: {}".format(target),
            allow_module_level=True,
        )

if not REPO_ROOT.exists():
    pytest.skip(
        "Repository root does not exist: {}".format(REPO_ROOT),
        allow_module_level=True,
    )

src_pkg_init = REPO_ROOT / "src" / PACKAGE_NAME / "__init__.py"
root_pkg_init = REPO_ROOT / PACKAGE_NAME / "__init__.py"

if src_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT / "src"))
elif root_pkg_init.exists():
    sys.path.insert(0, str(REPO_ROOT))
else:
    pytest.skip(
        "Could not find '{}' package under repo root. Expected {} or {}.".format(
            PACKAGE_NAME, src_pkg_init, root_pkg_init
        ),
        allow_module_level=True,
    )

import imageio.v3 as iio  # type: ignore  # noqa: E402


def _make_color_image(height: int = 32, width: int = 48) -> np.ndarray:
    """Create a small RGB test image as a uint8 NumPy array."""
    rng = np.random.default_rng(12345)
    return rng.integers(0, 256, size=(height, width, 3), dtype=np.uint8)


def _make_grayscale_frames(num_frames: int = 5, height: int = 16, width: int = 16) -> np.ndarray:
    """Create a stack of grayscale frames as a uint8 NumPy array."""
    rng = np.random.default_rng(9876)
    frames: List[np.ndarray] = []
    for _idx in range(num_frames):
        frame = rng.integers(0, 256, size=(height, width), dtype=np.uint8)
        frames.append(frame)
    return np.stack(frames, axis=0)


def test_png_roundtrip_with_imread_and_imwrite(tmp_path: Path) -> None:
    """Exercise a simple PNG roundtrip and verify image shape and data."""
    img = _make_color_image()
    path = tmp_path / "test.png"

    iio.imwrite(path, img)
    assert path.exists()

    loaded = iio.imread(path)
    assert isinstance(loaded, np.ndarray)
    assert loaded.shape == img.shape
    assert loaded.dtype == img.dtype
    np.testing.assert_array_equal(loaded, img)


def test_gif_multiframe_roundtrip_with_imiter(tmp_path: Path) -> None:
    """Write a small animated GIF and iterate frames using imiter."""
    frames = _make_grayscale_frames(num_frames=6, height=24, width=24)
    path = tmp_path / "anim.gif"

    iio.imwrite(path, frames)
    assert path.exists()

    loaded_frames = list(iio.imiter(path))
    assert len(loaded_frames) == frames.shape[0]

    h, w = frames.shape[1], frames.shape[2]
    for frame in loaded_frames:
        assert isinstance(frame, np.ndarray)
        assert frame.shape[0] == h
        assert frame.shape[1] == w


def test_improps_and_immeta_basic_fields(tmp_path: Path) -> None:
    """Check that improps and immeta expose basic metadata for a PNG image."""
    img = _make_color_image(height=40, width=50)
    path = tmp_path / "meta_test.png"

    iio.imwrite(path, img)
    assert path.exists()

    props = iio.improps(path)
    assert tuple(props.shape) == img.shape
    assert props.dtype == img.dtype

    meta = iio.immeta(path)
    assert isinstance(meta, dict)
    assert "mode" in meta
    assert isinstance(meta["mode"], str)


# ----------------------------
# Added functional test cases
# ----------------------------

def test_png_roundtrip_via_bytes_buffer() -> None:
    """Write PNG to in-memory bytes, then read back using extension."""
    img = _make_color_image(height=20, width=31)

    blob = iio.imwrite("<bytes>", img, extension=".png")
    assert isinstance(blob, (bytes, bytearray))
    assert len(blob) > 0

    loaded = iio.imread(blob, extension=".png")
    assert isinstance(loaded, np.ndarray)
    assert loaded.shape == img.shape
    assert loaded.dtype == img.dtype
    np.testing.assert_array_equal(loaded, img)


def test_png_imiter_yields_single_frame_equal_to_image(tmp_path: Path) -> None:
    """For a single-image PNG, imiter should yield exactly one frame."""
    img = _make_color_image(height=18, width=22)
    path = tmp_path / "single.png"

    iio.imwrite(path, img)
    assert path.exists()

    frames = list(iio.imiter(path))
    assert len(frames) == 1
    assert isinstance(frames[0], np.ndarray)
    assert frames[0].shape == img.shape
    np.testing.assert_array_equal(frames[0], img)


def test_png_imread_accepts_path_and_str_equivalently(tmp_path: Path) -> None:
    """Read the same PNG via Path and str(path) and verify identical content."""
    img = _make_color_image(height=25, width=27)
    path = tmp_path / "path_vs_str.png"

    iio.imwrite(path, img)
    assert path.exists()

    a = iio.imread(path)
    b = iio.imread(str(path))

    assert isinstance(a, np.ndarray)
    assert isinstance(b, np.ndarray)
    assert a.shape == b.shape == img.shape
    assert a.dtype == b.dtype == img.dtype
    np.testing.assert_array_equal(a, b)
    np.testing.assert_array_equal(a, img)


def test_gif_imread_returns_stack_with_expected_frame_count(tmp_path: Path) -> None:
    """Reading a GIF via imread should produce a stack/sequence with the right number of frames."""
    frames = _make_grayscale_frames(num_frames=5, height=20, width=21)
    path = tmp_path / "stack.gif"

    iio.imwrite(path, frames)
    assert path.exists()

    loaded = iio.imread(path)
    assert isinstance(loaded, np.ndarray)
    assert loaded.shape[0] == frames.shape[0]
    assert loaded.dtype == np.uint8


def test_gif_imread_index0_matches_first_imiter_frame_shape(tmp_path: Path) -> None:
    """Read first GIF frame using both index=0 and imiter; verify consistent spatial shape."""
    frames = _make_grayscale_frames(num_frames=4, height=19, width=23)
    path = tmp_path / "index0.gif"

    iio.imwrite(path, frames)
    assert path.exists()

    first_by_index = iio.imread(path, index=0)
    first_by_imiter = next(iter(iio.imiter(path)))

    assert isinstance(first_by_index, np.ndarray)
    assert isinstance(first_by_imiter, np.ndarray)
    assert first_by_index.shape[0] == first_by_imiter.shape[0]
    assert first_by_index.shape[1] == first_by_imiter.shape[1]
    assert first_by_index.dtype == first_by_imiter.dtype


def test_imopen_write_then_read_png(tmp_path: Path) -> None:
    """Use the v3 imopen context manager to write then read a PNG."""
    img = _make_color_image(height=16, width=20)
    path = tmp_path / "imopen.png"

    with iio.imopen(path, "w") as f:
        f.write(img)
    assert path.exists()

    with iio.imopen(path, "r") as f:
        loaded = f.read()

    assert isinstance(loaded, np.ndarray)
    assert loaded.shape == img.shape
    assert loaded.dtype == img.dtype
    np.testing.assert_array_equal(loaded, img)


def test_improps_for_gif_has_expected_spatial_dimensions(tmp_path: Path) -> None:
    """improps on a GIF should include the written frame height/width in its reported shape.

    In practice, different plugins/paths can report shapes like:
      - (T, H, W)
      - (T, H, W, C)
      - (H, W, C)
      - (W, H, C)
    Therefore we validate that the expected H and W appear somewhere in props.shape,
    without assuming their exact positions.
    """
    frames = _make_grayscale_frames(num_frames=3, height=17, width=19)
    path = tmp_path / "props.gif"

    iio.imwrite(path, frames)
    assert path.exists()

    props = iio.improps(path)
    shape = tuple(int(x) for x in tuple(props.shape))

    assert len(shape) >= 2
    assert all(x > 0 for x in shape)

    expected_h = int(frames.shape[1])
    expected_w = int(frames.shape[2])

    assert expected_h in shape
    assert expected_w in shape
    assert props.dtype == np.uint8
