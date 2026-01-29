from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Union

from PIL import Image


def ensure_image(image: Union[str, Image.Image]) -> Image.Image:
    if isinstance(image, Image.Image):
        return image
    return Image.open(image)


def image_to_rgb_if_needed(img: Image.Image, auto_convert_rgb: bool = False) -> Image.Image:
    """
    Ensure image is in a channel-based mode suitable for LSB operations.
    If auto_convert_rgb is True, convert unsupported modes to RGB.
    """
    if img.mode in ("RGB", "RGBA", "L"):
        return img
    if auto_convert_rgb:
        return img.convert("RGB")
    raise ValueError(f"Unsupported image mode {img.mode}. Use auto_convert_rgb=True to convert.")


def text_to_bytes(message: str, encoding: str = "UTF-8") -> bytes:
    return message.encode(encoding)


def bytes_to_text(data: bytes, encoding: str = "UTF-8") -> str:
    return data.decode(encoding, errors="strict")


def int_to_bits(value: int, width: int) -> List[int]:
    return [((value >> i) & 1) for i in range(width - 1, -1, -1)]


def bits_to_int(bits: List[int]) -> int:
    v = 0
    for b in bits:
        v = (v << 1) | (1 if b else 0)
    return v


def get_image_pixels_flat(img: Image.Image) -> Tuple[List[int], Dict[str, Any]]:
    """
    Flatten pixels into a list of channel integers and return metadata needed to restore.
    Supports RGB, RGBA, and L.
    """
    mode = img.mode
    w, h = img.size

    if mode == "L":
        data = list(img.getdata())
        meta = {"mode": "L", "size": (w, h)}
        return data, meta

    if mode in ("RGB", "RGBA"):
        pixels = list(img.getdata())
        channels: List[int] = []
        for p in pixels:
            channels.extend(list(p))
        meta = {"mode": mode, "size": (w, h)}
        return channels, meta

    raise ValueError(f"Unsupported image mode {mode}")


def set_image_pixels_flat(img: Image.Image, channels: List[int], meta: Dict[str, Any]) -> Image.Image:
    mode = meta["mode"]
    size = meta["size"]
    out = Image.new(mode, size)

    if mode == "L":
        out.putdata(channels)
        return out

    if mode in ("RGB", "RGBA"):
        n = 3 if mode == "RGB" else 4
        pixels = [tuple(channels[i:i + n]) for i in range(0, len(channels), n)]
        out.putdata(pixels)
        return out

    raise ValueError(f"Unsupported image mode {mode}")