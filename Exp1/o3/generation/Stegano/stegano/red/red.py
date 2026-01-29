"""
stegano.red – Simple variant that hides data only in the red channel.

This module offers the same public API as `stegano.red` from the reference
library but uses a much simpler encoding strategy.
"""
from __future__ import annotations

import itertools
from typing import List

from PIL import Image

from ..tools.bititerator import BitReader, BitWriter
from ..tools.utils import bits_from_bytes, bytes_from_bits


def _prepare_image(img: Image.Image) -> Image.Image:
    if img.mode != "RGB":
        img = img.convert("RGB")
    return img.copy()


def hide(image: Image.Image, message: str, encoding: str = "UTF-8") -> Image.Image:
    """
    Hides *message* in the LSB of the red channel of *image*.
    """
    img = _prepare_image(image)
    width, height = img.size
    capacity = width * height  # 1 bit per pixel

    message_bytes = message.encode(encoding)
    payload_bits = bits_from_bytes(len(message_bytes).to_bytes(4, "big"))
    payload_bits.extend(bits_from_bytes(message_bytes))

    if len(payload_bits) > capacity:
        raise ValueError("Message too large for selected image.")

    pixels: List[tuple[int, int, int]] = list(img.getdata())

    for idx, bit in enumerate(payload_bits):
        r, g, b = pixels[idx]
        r = (r & ~1) | bit
        pixels[idx] = (r, g, b)

    img_out = Image.new("RGB", img.size)
    img_out.putdata(pixels)
    return img_out


def reveal(image: Image.Image, encoding: str = "UTF-8") -> str:
    """
    Extracts a message from the LSB of the red channel of *image*.
    """
    img = _prepare_image(image)
    pixels: List[tuple[int, int, int]] = list(img.getdata())

    bits = [(r & 1) for r, _, _ in pixels]

    length_bits = bits[:32]
    msg_len = int.from_bytes(bytes_from_bits(length_bits), "big")

    message_bits = bits[32 : 32 + msg_len * 8]
    message_bytes = bytes_from_bits(message_bits)
    return message_bytes.decode(encoding)