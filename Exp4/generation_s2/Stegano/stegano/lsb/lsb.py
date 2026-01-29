from __future__ import annotations

from typing import Callable, Iterator, Optional, Union

from PIL import Image

from stegano.tools.bititerator import (
    bits_from_bytes,
    bytes_from_bits,
    int_to_bits,
)
from stegano.tools.utils import (
    ensure_image,
    image_to_rgb_if_needed,
    iter_channel_values,
    set_channel_lsb,
)


_SENTINEL = b"\x00\xff\x00\xff\x00\xff"  # unlikely marker
_LEN_BITS = 32  # payload length in bytes, unsigned 32-bit


def _iter_positions(
    capacity: int,
    generator: Optional[Iterator[int]],
    shift: int,
) -> Iterator[int]:
    if generator is None:
        # Sequential indices
        for i in range(shift, capacity):
            yield i
        return

    # Use generator values as indices; apply shift; filter within capacity.
    # Ensure we eventually terminate by only yielding indices < capacity.
    for idx in generator:
        pos = idx + shift
        if 0 <= pos < capacity:
            yield pos
        # if >= capacity, skip; generator may produce more, keep going.


def hide(
    image,
    message,
    generator: Optional[Iterator[int]] = None,
    shift: int = 0,
    encoding: str = "UTF-8",
    auto_convert_rgb: bool = False,
) -> Image.Image:
    """
    Hide a text message in the least significant bits of an image.

    Parameters match the reference project core API.
    """
    img = ensure_image(image)
    if auto_convert_rgb:
        img = image_to_rgb_if_needed(img)

    if isinstance(message, str):
        payload = message.encode(encoding)
    else:
        # allow bytes-like
        payload = bytes(message)

    header = int.to_bytes(len(payload), 4, "big") + _SENTINEL
    data = header + payload

    bits = list(bits_from_bytes(data))

    # Capacity: number of writable channels (we use all channels except alpha)
    channels = list(iter_channel_values(img))
    capacity = len(channels)
    if len(bits) > capacity:
        raise ValueError("Message too large to hide in this image.")

    out = img.copy()
    out_pixels = out.load()

    positions = _iter_positions(capacity=capacity, generator=generator, shift=shift)

    # We need a mapping from linear channel index -> (x,y,channel_index_within_pixel)
    # Build a lightweight index of coordinates and channel ids.
    width, height = out.size
    mode = out.mode
    # Determine channels per pixel excluding alpha
    if mode in ("RGB", "RGBA"):
        usable_channels = 3
    elif mode in ("L", "P"):
        usable_channels = 1
    elif mode in ("LA",):
        usable_channels = 1
    else:
        # fallback: convert to RGB to proceed if supported
        if auto_convert_rgb:
            out = out.convert("RGB")
            out_pixels = out.load()
            width, height = out.size
            mode = out.mode
            usable_channels = 3
        else:
            raise ValueError(f"Unsupported image mode for LSB steganography: {mode}")

    def get_loc_from_linear(n: int):
        pixel_index, chan = divmod(n, usable_channels)
        x = pixel_index % width
        y = pixel_index // width
        return x, y, chan

    for bit in bits:
        pos = next(positions)
        x, y, chan = get_loc_from_linear(pos)
        px = out_pixels[x, y]
        # Normalize to tuple
        if usable_channels == 1:
            new_val = set_channel_lsb(int(px if not isinstance(px, tuple) else px[0]), bit)
            if isinstance(px, tuple):
                # Preserve other channels (e.g., alpha)
                if len(px) == 2:  # LA
                    out_pixels[x, y] = (new_val, px[1])
                else:
                    out_pixels[x, y] = (new_val,)
            else:
                out_pixels[x, y] = new_val
        else:
            if not isinstance(px, tuple):
                # should not happen for RGB/RGBA
                px = (px, px, px)
            px_list = list(px)
            px_list[chan] = set_channel_lsb(px_list[chan], bit)
            out_pixels[x, y] = tuple(px_list)

    return out


def reveal(
    image,
    generator: Optional[Iterator[int]] = None,
    shift: int = 0,
    encoding: str = "UTF-8",
) -> str:
    """
    Reveal a text message hidden by stegano.lsb.hide.
    """
    img = ensure_image(image)

    # Build a list of all usable channel values in deterministic order
    channels = list(iter_channel_values(img))
    capacity = len(channels)

    positions = _iter_positions(capacity=capacity, generator=generator, shift=shift)

    # Read header: 4 bytes length + sentinel
    header_len = 4 + len(_SENTINEL)
    header_bits_len = header_len * 8

    header_bits = []
    for _ in range(header_bits_len):
        pos = next(positions)
        header_bits.append(channels[pos] & 1)

    header_bytes = bytes(bytes_from_bits(header_bits))
    msg_len = int.from_bytes(header_bytes[:4], "big", signed=False)
    sentinel = header_bytes[4:]
    if sentinel != _SENTINEL:
        raise ValueError("No hidden message found (invalid sentinel).")

    # Read message bits
    msg_bits_len = msg_len * 8
    if header_bits_len + msg_bits_len > capacity:
        raise ValueError("Corrupted hidden message (declared size too large).")

    msg_bits = []
    for _ in range(msg_bits_len):
        pos = next(positions)
        msg_bits.append(channels[pos] & 1)

    msg_bytes = bytes(bytes_from_bits(msg_bits))
    return msg_bytes.decode(encoding, errors="strict")