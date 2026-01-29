from __future__ import annotations

from typing import Union

from PIL import Image

from stegano.tools.bititerator import bytes_to_bits, bits_to_bytes
from stegano.tools.utils import ensure_image, frame_payload, parse_length_prefix_from_bits, validate_length_against_capacity_bytes


def _ensure_rgb_or_rgba(img: Image.Image) -> Image.Image:
    if img.mode in ("RGB", "RGBA"):
        return img
    return img.convert("RGB")


def hide(image: Union[str, Image.Image], message: str) -> Image.Image:
    img = _ensure_rgb_or_rgba(ensure_image(image))
    out = img.copy()
    w, h = out.size

    payload = frame_payload(message.encode("UTF-8"))
    bits = list(bytes_to_bits(payload))
    capacity = w * h  # one bit per pixel (red channel)
    if len(bits) > capacity:
        raise ValueError("Message too large to hide in image (insufficient capacity).")

    px = out.load()
    i = 0
    for y in range(h):
        for x in range(w):
            if i >= len(bits):
                return out
            bit = bits[i]
            i += 1
            p = px[x, y]
            if out.mode == "RGB":
                r, g, b = p
                r = (r & 0xFE) | bit
                px[x, y] = (r, g, b)
            else:
                r, g, b, a = p
                r = (r & 0xFE) | bit
                px[x, y] = (r, g, b, a)
    return out


def reveal(image: Union[str, Image.Image]) -> str:
    img = _ensure_rgb_or_rgba(ensure_image(image))
    w, h = img.size
    px = img.load()

    def bits_iter():
        for y in range(h):
            for x in range(w):
                p = px[x, y]
                r = p[0]
                yield (r & 1)

    it = bits_iter()
    length, length_bits_consumed = parse_length_prefix_from_bits(it)
    remaining_bits = (w * h) - length_bits_consumed
    validate_length_against_capacity_bytes(length, remaining_bits)

    payload_bits = [next(it) for _ in range(length * 8)]
    payload = bits_to_bytes(payload_bits)
    return payload.decode("UTF-8")