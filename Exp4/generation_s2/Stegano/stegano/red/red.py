from __future__ import annotations

from PIL import Image

from stegano.tools.bititerator import bits_from_bytes, bytes_from_bits
from stegano.tools.utils import ensure_image, image_to_rgb_if_needed, set_channel_lsb

_SENTINEL = b"\x00\xff\x00\xff"
_LEN_BITS = 32


def hide(image, message) -> Image.Image:
    img = ensure_image(image)
    img = image_to_rgb_if_needed(img)

    if isinstance(message, str):
        payload = message.encode("utf-8")
    else:
        payload = bytes(message)

    header = int.to_bytes(len(payload), 4, "big") + _SENTINEL
    data = header + payload
    bits = list(bits_from_bytes(data))

    width, height = img.size
    capacity = width * height  # 1 bit per pixel (red channel)
    if len(bits) > capacity:
        raise ValueError("Message too large to hide in red channel.")

    out = img.copy()
    px = out.load()

    i = 0
    for y in range(height):
        for x in range(width):
            if i >= len(bits):
                return out
            r, g, b = px[x, y]
            r2 = set_channel_lsb(r, bits[i])
            px[x, y] = (r2, g, b)
            i += 1

    return out


def reveal(image) -> str:
    img = ensure_image(image)
    img = image_to_rgb_if_needed(img)

    width, height = img.size
    px = img.load()

    def red_lsb_stream():
        for y in range(height):
            for x in range(width):
                r = px[x, y][0]
                yield (r & 1)

    stream = red_lsb_stream()

    header_len = 4 + len(_SENTINEL)
    header_bits = [next(stream) for _ in range(header_len * 8)]
    header = bytes(bytes_from_bits(header_bits))

    msg_len = int.from_bytes(header[:4], "big", signed=False)
    if header[4:] != _SENTINEL:
        raise ValueError("No hidden message found (invalid sentinel).")

    msg_bits = [next(stream) for _ in range(msg_len * 8)]
    msg = bytes(bytes_from_bits(msg_bits))
    return msg.decode("utf-8", errors="strict")