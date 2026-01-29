"""
stegano.lsb – Generic least-significant-bit image steganography
"""
from __future__ import annotations

import itertools
import math
from typing import Callable, Iterator, List, Sequence

from PIL import Image

from .generators import eratosthenes
from ..tools.bititerator import BitReader, BitWriter
from ..tools.utils import bytes_from_bits, bits_from_bytes


GeneratorFactory = Callable[[], Iterator[int]]


def _prepare_image(
    image: Image.Image, *, auto_convert_rgb: bool = False
) -> Image.Image:
    """
    Makes sure the supplied image is in RGB mode (3×8-bit) because the current
    implementation depends on that layout.
    """
    if image.mode != "RGB":
        if not auto_convert_rgb:
            raise ValueError(
                f"Unsupported image mode {image.mode!r}. "
                "Pass auto_convert_rgb=True to force conversion."
            )
        image = image.convert("RGB")
    return image.copy()  # never mutate caller-owned instance


def _capacity_in_bits(img: Image.Image) -> int:
    width, height = img.size
    return width * height * 3  # RGB – 1 bit per colour component


def _iter_indices(
    generator_factory: GeneratorFactory | None, pixel_count: int, shift: int
) -> Iterator[int]:
    """
    Returns an iterator of pixel indices either by using a user supplied
    generator factory or – if *None* – a simple ``range(pixel_count)``.
    """
    if generator_factory is None:
        iterable: Iterator[int] = iter(range(pixel_count))
    else:
        iterable = generator_factory()
    # Skip initial *shift* indices
    for _ in range(shift):
        try:
            next(iterable)
        except StopIteration:
            raise ValueError("Shift larger than number of pixel positions") from None
    return iterable


def hide(
    image: Image.Image,
    message: str,
    generator: GeneratorFactory | None = None,
    shift: int = 0,
    encoding: str = "UTF-8",
    auto_convert_rgb: bool = False,
) -> Image.Image:
    """
    Returns a *new* ``PIL.Image.Image`` instance with *message* embedded.

    The binary payload is ``len(message_bytes)`` (32-bit big-endian) followed by
    the encoded message bytes.  One bit is stored in the least significant bit
    of every colour component (R, G, B).

    Parameters
    ----------
    image:
        Source image.
    message:
        Text message that will be hidden.
    generator:
        A callable with no arguments returning an iterator of *pixel indices*.
        Defaults to using sequential order.
    shift:
        Skip the first *shift* indices emitted by the generator.
    encoding:
        Character encoding – identical for hide/reveal.
    auto_convert_rgb:
        If *True* non-RGB images are converted automatically.  Otherwise an
        exception is raised.
    """
    img = _prepare_image(image, auto_convert_rgb=auto_convert_rgb)

    message_bytes = message.encode(encoding, errors="strict")
    payload_bits = bits_from_bytes(len(message_bytes).to_bytes(4, "big"))
    payload_bits.extend(bits_from_bytes(message_bytes))

    capacity = _capacity_in_bits(img)
    if len(payload_bits) > capacity:
        raise ValueError(
            f"Message too large – requires {len(payload_bits)} bits, "
            f"but only {capacity} bits available."
        )

    flat: List[int] = list(img.getdata())  # [(r,g,b), ...]
    # Flatten channel values into one list [r0,g0,b0, r1,g1,b1, ...]
    channels: List[int] = list(itertools.chain.from_iterable(flat))

    pixel_count = len(flat)
    index_iter = _iter_indices(generator, pixel_count, shift)

    writer = BitWriter(iter(payload_bits))

    # Embed payload
    try:
        for pixel_index in index_iter:
            base = pixel_index * 3
            for ch in range(3):
                bit = writer.read_bit()
                channels[base + ch] = (channels[base + ch] & ~1) | bit
    except StopIteration:
        # Payload finished – exit loop early
        pass

    # Reconstruct list[(R, G, B)]
    it = iter(channels)
    new_pixels = list(zip(it, it, it))
    img_out = Image.new("RGB", img.size)
    img_out.putdata(new_pixels)
    return img_out


def reveal(
    image: Image.Image,
    generator: GeneratorFactory | None = None,
    shift: int = 0,
    encoding: str = "UTF-8",
) -> str:
    """
    Extracts a hidden text message from *image* (must match the parameters used
    during the *hide* call).
    """
    img = _prepare_image(image, auto_convert_rgb=False)

    flat = list(img.getdata())
    channels: List[int] = list(itertools.chain.from_iterable(flat))

    pixel_count = len(flat)
    index_iter = _iter_indices(generator, pixel_count, shift)

    bits: List[int] = []

    # First read 32-bit message length
    for _ in range(32):
        pixel_index = next(index_iter)
        ch_offset = (_ % 3)  # 0,1,2
        if _ % 3 == 0 and _:
            # Once every 3 bits we need to advance to next pixel from iterator
            pass
        base = pixel_index * 3 + ch_offset
        bits.append(channels[base] & 1)

    length_bytes = bytes_from_bits(bits)
    msg_len = int.from_bytes(length_bytes, "big")

    total_bits = msg_len * 8
    bits.clear()

    for _ in range(total_bits):
        pixel_index = next(index_iter)
        ch_offset = (_ % 3)
        base = pixel_index * 3 + ch_offset
        bits.append(channels[base] & 1)

    message_bytes = bytes_from_bits(bits)
    return message_bytes.decode(encoding, errors="strict")