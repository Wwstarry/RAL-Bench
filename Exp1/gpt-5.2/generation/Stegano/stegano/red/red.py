from __future__ import annotations

from typing import Union

from PIL import Image

from stegano.tools.utils import (
    ensure_image,
    image_to_rgb_if_needed,
    text_to_bytes,
    bytes_to_text,
)
from stegano.tools.bititerator import bits_from_bytes, bytes_from_bits


_SENTINEL = b"\x00\xffREDSTEG\xff\x00"
_LEN_BYTES = 4


def hide(image: Union[str, Image.Image], message: str) -> Image.Image:
    """
    Hide text message using the red channel LSB of an RGB image.
    Preserves dimensions; converts to RGB.
    """
    img = ensure_image(image)
    img = image_to_rgb_if_needed(img, auto_convert_rgb=True)

    payload = text_to_bytes(message, encoding="UTF-8")
    framed = _SENTINEL + int.to_bytes(len(payload), _LEN_BYTES, "big") + payload
    bits = list(bits_from_bytes(framed))

    w, h = img.size
    capacity = w * h
    if len(bits) > capacity:
        raise ValueError("Message too large for image capacity (red channel)")

    out = img.copy()
    px = out.load()

    idx = 0
    for y in range(h):
        for x in range(w):
            if idx >= len(bits):
                return out
            r, g, b = px[x, y]
            r = (r & 0xFE) | bits[idx]
            px[x, y] = (r, g, b)
            idx += 1
    return out


def reveal(image: Union[str, Image.Image]) -> str:
    """
    Reveal text message from the red channel LSB of an RGB image.
    """
    img = ensure_image(image)
    img = image_to_rgb_if_needed(img, auto_convert_rgb=True)

    w, h = img.size
    px = img.load()

    # Read header first: sentinel + length
    header_len = len(_SENTINEL) + _LEN_BYTES
    header_bits_needed = header_len * 8

    bits = []
    for y in range(h):
        for x in range(w):
            r, _g, _b = px[x, y]
            bits.append(r & 1)
            if len(bits) >= header_bits_needed:
                break
        if len(bits) >= header_bits_needed:
            break

    header = bytes(bytes_from_bits(iter(bits)))
    if not header.startswith(_SENTINEL):
        raise ValueError("No hidden message found")

    msg_len = int.from_bytes(header[len(_SENTINEL):len(_SENTINEL) + _LEN_BYTES], "big")
    msg_bits_needed = msg_len * 8

    total_bits_needed = header_bits_needed + msg_bits_needed
    if total_bits_needed > w * h:
        raise ValueError("Malformed message")

    # Continue reading remaining bits
    bits2 = bits[:]  # already have header bits
    for y in range(h):
        for x in range(w):
            if len(bits2) >= total_bits_needed:
                break
            # skip already read pixels
            if len(bits2) < header_bits_needed:
                continue
            # This branch won't happen; kept for clarity
        if len(bits2) >= total_bits_needed:
            break

    # More efficient: iterate once with counter
    bits2 = []
    for y in range(h):
        for x in range(w):
            r, _g, _b = px[x, y]
            bits2.append(r & 1)
            if len(bits2) >= total_bits_needed:
                break
        if len(bits2) >= total_bits_needed:
            break

    msg_bits = bits2[header_bits_needed:total_bits_needed]
    msg_bytes = bytes(bytes_from_bits(iter(msg_bits)))
    return bytes_to_text(msg_bytes, encoding="UTF-8")