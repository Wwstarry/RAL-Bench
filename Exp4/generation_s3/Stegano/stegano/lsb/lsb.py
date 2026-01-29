from __future__ import annotations

from typing import Iterable, Iterator, Optional, Sequence, Tuple, Union

from PIL import Image

from stegano.tools.bititerator import bits_from_bytes, bytes_from_bits
from stegano.tools.utils import (
    DEFAULT_TERMINATOR,
    ensure_image,
    find_terminator_index,
    iter_channel_positions,
)


ImageInput = Union[str, Image.Image]


def _get_mode_channels(mode: str) -> Tuple[str, ...]:
    # We support "L", "RGB", "RGBA" (but do not write to alpha).
    if mode == "L":
        return ("L",)
    if mode == "RGB":
        return ("R", "G", "B")
    if mode == "RGBA":
        return ("R", "G", "B")  # keep alpha untouched
    raise ValueError(f"Unsupported image mode: {mode!r}")


def _capacity_bits(img: Image.Image, channels: Sequence[str]) -> int:
    w, h = img.size
    return w * h * len(channels)


def _iter_positions_sequential(img: Image.Image, channels: Sequence[str]) -> Iterator[Tuple[int, int, int]]:
    w, h = img.size
    for y in range(h):
        for x in range(w):
            for c in range(len(channels)):
                yield (x, y, c)


def _iter_positions_generator(
    img: Image.Image,
    channels: Sequence[str],
    generator: Iterable[int],
    shift: int,
) -> Iterator[Tuple[int, int, int]]:
    """
    Convert a pixel-index generator into per-channel positions.
    Each pixel index yields up to len(channels) embedding positions.
    """
    w, h = img.size
    n_pixels = w * h
    for idx in generator:
        pixel_index = idx + shift
        if pixel_index < 0 or pixel_index >= n_pixels:
            # Reference behavior isn't fully specified; skipping out-of-range keeps iterator usable.
            # This also avoids infinite loops if a generator yields small primes with huge shift.
            continue
        x = pixel_index % w
        y = pixel_index // w
        for c in range(len(channels)):
            yield (x, y, c)


def hide(
    image: ImageInput,
    message: Union[str, bytes],
    generator: Optional[Iterable[int]] = None,
    shift: int = 0,
    encoding: str = "UTF-8",
    auto_convert_rgb: bool = False,
) -> Image.Image:
    img = ensure_image(image)

    if img.mode not in ("L", "RGB", "RGBA"):
        if auto_convert_rgb:
            img = img.convert("RGB")
        else:
            raise ValueError(f"Unsupported image mode {img.mode!r}. Use auto_convert_rgb=True to convert.")
    channels = _get_mode_channels(img.mode)

    if isinstance(message, str):
        payload = message.encode(encoding)
    elif isinstance(message, (bytes, bytearray)):
        payload = bytes(message)
    else:
        raise TypeError("message must be str or bytes")

    payload += DEFAULT_TERMINATOR
    required_bits = len(payload) * 8
    capacity = _capacity_bits(img, channels)
    if required_bits > capacity:
        raise ValueError("Insufficient capacity to hide message in image.")

    out = img.copy()
    pixels = out.load()

    bit_iter = iter(bits_from_bytes(payload))
    if generator is None:
        pos_iter = _iter_positions_sequential(out, channels)
    else:
        pos_iter = _iter_positions_generator(out, channels, generator, shift)

    # Write bits
    for (x, y, c) in pos_iter:
        try:
            bit = next(bit_iter)
        except StopIteration:
            break

        px = pixels[x, y]
        if out.mode == "L":
            val = int(px)
            val = (val & ~1) | bit
            pixels[x, y] = val
        elif out.mode in ("RGB", "RGBA"):
            if out.mode == "RGB":
                r, g, b = px
                rgb = [r, g, b]
                rgb[c] = (int(rgb[c]) & ~1) | bit
                pixels[x, y] = tuple(rgb)
            else:
                r, g, b, a = px
                rgb = [r, g, b]
                rgb[c] = (int(rgb[c]) & ~1) | bit
                pixels[x, y] = (rgb[0], rgb[1], rgb[2], a)
        else:
            # should not happen due to checks
            raise ValueError(f"Unsupported image mode: {out.mode!r}")

    # Ensure all bits were written (generator could be too sparse due to skipping OOR indices)
    try:
        next(bit_iter)
        raise ValueError("Insufficient usable capacity with provided generator/shift to hide message.")
    except StopIteration:
        pass

    return out


def reveal(
    image: ImageInput,
    generator: Optional[Iterable[int]] = None,
    shift: int = 0,
    encoding: str = "UTF-8",
) -> str:
    img = ensure_image(image)
    if img.mode not in ("L", "RGB", "RGBA"):
        raise ValueError(f"Unsupported image mode: {img.mode!r}")

    channels = _get_mode_channels(img.mode)
    pixels = img.load()

    if generator is None:
        pos_iter = _iter_positions_sequential(img, channels)
    else:
        pos_iter = _iter_positions_generator(img, channels, generator, shift)

    bits = []
    collected = bytearray()

    # Read bits and build bytes incrementally to detect terminator early
    for (x, y, c) in pos_iter:
        px = pixels[x, y]
        if img.mode == "L":
            val = int(px)
        elif img.mode == "RGB":
            val = int(px[c])
        else:  # RGBA but we only read RGB channels
            val = int(px[c])

        bits.append(val & 1)
        if len(bits) == 8:
            collected.extend(bytes_from_bits(bits))
            bits.clear()
            idx = find_terminator_index(collected, DEFAULT_TERMINATOR)
            if idx != -1:
                data = bytes(collected[:idx])
                return data.decode(encoding)

    raise ValueError("No hidden message found (terminator not present).")