from __future__ import annotations

from typing import Union

from PIL import Image

from stegano.tools.bititerator import bits_from_bytes, bytes_from_bits
from stegano.tools.utils import DEFAULT_TERMINATOR, ensure_image, find_terminator_index

ImageInput = Union[str, Image.Image]


def hide(image: ImageInput, message: str) -> Image.Image:
    img = ensure_image(image).convert("RGB")
    payload = message.encode("UTF-8") + DEFAULT_TERMINATOR
    required_bits = len(payload) * 8

    w, h = img.size
    capacity = w * h  # 1 bit per pixel (red channel LSB)
    if required_bits > capacity:
        raise ValueError("Insufficient capacity to hide message in red channel.")

    out = img.copy()
    pixels = out.load()

    bit_iter = iter(bits_from_bytes(payload))
    for y in range(h):
        for x in range(w):
            try:
                bit = next(bit_iter)
            except StopIteration:
                return out
            r, g, b = pixels[x, y]
            r = (int(r) & ~1) | bit
            pixels[x, y] = (r, g, b)

    # If we didn't return, we ran out of pixels
    raise ValueError("Insufficient capacity to hide message in red channel.")


def reveal(image: ImageInput) -> str:
    img = ensure_image(image).convert("RGB")
    w, h = img.size
    pixels = img.load()

    bits = []
    collected = bytearray()

    for y in range(h):
        for x in range(w):
            r, g, b = pixels[x, y]
            bits.append(int(r) & 1)
            if len(bits) == 8:
                collected.extend(bytes_from_bits(bits))
                bits.clear()
                idx = find_terminator_index(collected, DEFAULT_TERMINATOR)
                if idx != -1:
                    return bytes(collected[:idx]).decode("UTF-8")

    raise ValueError("No hidden message found (terminator not present).")