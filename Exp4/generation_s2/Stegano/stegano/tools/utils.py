from __future__ import annotations

from typing import Iterator, Union

from PIL import Image


def ensure_image(image) -> Image.Image:
    """Accept a PIL.Image.Image or a path-like and return an opened image."""
    if isinstance(image, Image.Image):
        return image
    return Image.open(image)


def image_to_rgb_if_needed(img: Image.Image) -> Image.Image:
    """Convert paletted/LA/etc to RGB while preserving size."""
    if img.mode == "RGB":
        return img
    if img.mode == "RGBA":
        # keep alpha if present; LSB backend can handle RGBA but red backend expects RGB
        return img.convert("RGB")
    if img.mode in ("P", "L", "LA"):
        return img.convert("RGB")
    return img.convert("RGB")


def set_channel_lsb(value: int, bit: int) -> int:
    """Replace the least significant bit of an 8-bit channel value."""
    return (int(value) & 0xFE) | (1 if bit else 0)


def iter_channel_values(img: Image.Image) -> Iterator[int]:
    """
    Iterate over usable channel values (integers) in deterministic order for LSB.
    Excludes alpha channel when present.
    """
    mode = img.mode
    px = img.load()
    width, height = img.size

    if mode == "RGB":
        for y in range(height):
            for x in range(width):
                r, g, b = px[x, y]
                yield r
                yield g
                yield b
        return

    if mode == "RGBA":
        for y in range(height):
            for x in range(width):
                r, g, b, a = px[x, y]
                yield r
                yield g
                yield b
        return

    if mode == "L":
        for y in range(height):
            for x in range(width):
                v = px[x, y]
                yield int(v)
        return

    if mode == "LA":
        for y in range(height):
            for x in range(width):
                v, a = px[x, y]
                yield int(v)
        return

    if mode == "P":
        # Convert palette index stream as indices (not RGB-expanded). This keeps size.
        # For robustness, caller may convert to RGB via auto_convert_rgb.
        for y in range(height):
            for x in range(width):
                yield int(px[x, y])
        return

    # Unknown: iterate after conversion to RGB to guarantee functionality
    rgb = img.convert("RGB")
    yield from iter_channel_values(rgb)