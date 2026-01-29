from __future__ import annotations

from typing import Iterable, Iterator, Optional, Tuple, Union

from PIL import Image

DEFAULT_TERMINATOR: bytes = b"\x00\xff\x00\xff\x00\xff\x00\xff"


def ensure_image(image: Union[str, Image.Image]) -> Image.Image:
    """
    Accept either a PIL.Image.Image or a path-like string.
    Returns a PIL image.
    """
    if isinstance(image, Image.Image):
        return image
    if isinstance(image, str):
        return Image.open(image)
    raise TypeError("image must be a PIL.Image.Image or a path string")


def find_terminator_index(data: Union[bytes, bytearray], terminator: bytes = DEFAULT_TERMINATOR) -> int:
    """
    Return the start index of terminator in data, or -1 if not found.
    """
    return bytes(data).find(terminator)


def iter_channel_positions(width: int, height: int, n_channels: int) -> Iterator[Tuple[int, int, int]]:
    """
    Helper to iterate (x,y,channel_index) in raster order.
    """
    for y in range(height):
        for x in range(width):
            for c in range(n_channels):
                yield (x, y, c)