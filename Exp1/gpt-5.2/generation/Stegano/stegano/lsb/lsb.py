from __future__ import annotations

from typing import Callable, Iterable, Iterator, Optional, Union

from PIL import Image

from stegano.tools.utils import (
    ensure_image,
    image_to_rgb_if_needed,
    get_image_pixels_flat,
    set_image_pixels_flat,
    int_to_bits,
    bits_to_int,
    text_to_bytes,
    bytes_to_text,
)
from stegano.tools.bititerator import bits_from_bytes, bytes_from_bits


_SENTINEL = b"\x00\xff\x00\xffSTEGANO\xff\x00\xff\x00"
_LEN_BITS = 32  # store payload length (in bytes) in 32 bits


def _positions_sequential(nbits: int, shift: int = 0) -> Iterator[int]:
    i = shift
    for _ in range(nbits):
        yield i
        i += 1


def _positions_from_generator(gen: Iterable[int], nbits: int, shift: int = 0) -> Iterator[int]:
    # Reference stegano uses generator values as positions; shift offsets them.
    it = iter(gen)
    for _ in range(nbits):
        yield next(it) + shift


def _validate_capacity(total_channels: int, required_bits: int) -> None:
    if required_bits > total_channels:
        raise ValueError("Message too large for image capacity")


def _hide_bits_in_channels(channels: list[int], bits: Iterator[int], positions: Iterator[int]) -> list[int]:
    out = channels[:]  # copy
    for b, pos in zip(bits, positions):
        if pos < 0 or pos >= len(out):
            raise ValueError("Generator produced position outside image capacity")
        out[pos] = (out[pos] & 0xFE) | (b & 1)
    return out


def _reveal_bits_from_channels(channels: list[int], nbits: int, positions: Iterator[int]) -> list[int]:
    out_bits: list[int] = []
    for _ in range(nbits):
        pos = next(positions)
        if pos < 0 or pos >= len(channels):
            raise ValueError("Generator produced position outside image capacity")
        out_bits.append(channels[pos] & 1)
    return out_bits


def hide(
    image: Union[str, Image.Image],
    message: str,
    generator: Optional[Iterable[int]] = None,
    shift: int = 0,
    encoding: str = "UTF-8",
    auto_convert_rgb: bool = False,
) -> Image.Image:
    """
    Hide a text message into the LSB of an image.

    Args:
        image: PIL Image or path.
        message: text to hide.
        generator: iterable of positions (e.g., stegano.lsb.generators.eratosthenes()).
        shift: integer offset added to each generated position.
        encoding: message encoding.
        auto_convert_rgb: if True, converts non-RGB/RGBA images to RGB.

    Returns:
        New PIL Image with the hidden message.
    """
    img = ensure_image(image)
    img = image_to_rgb_if_needed(img, auto_convert_rgb=auto_convert_rgb)

    payload = text_to_bytes(message, encoding=encoding)
    framed = _SENTINEL + int.to_bytes(len(payload), 4, "big") + payload

    channels, meta = get_image_pixels_flat(img)
    total = len(channels)

    required_bits = len(framed) * 8
    _validate_capacity(total, required_bits)

    bitstream = bits_from_bytes(framed)

    if generator is None:
        positions = _positions_sequential(required_bits, shift=shift)
    else:
        positions = _positions_from_generator(generator, required_bits, shift=shift)

    new_channels = _hide_bits_in_channels(channels, bitstream, positions)
    out_img = set_image_pixels_flat(img, new_channels, meta)
    return out_img


def reveal(
    image: Union[str, Image.Image],
    generator: Optional[Iterable[int]] = None,
    shift: int = 0,
    encoding: str = "UTF-8",
) -> str:
    """
    Reveal a hidden text message from an image.

    Args:
        image: PIL Image or path.
        generator: iterable of positions used during hide.
        shift: same shift used during hide.
        encoding: decode encoding.

    Returns:
        Extracted text (str). Raises ValueError if sentinel not found or malformed.
    """
    img = ensure_image(image)
    channels, _meta = get_image_pixels_flat(img)
    total = len(channels)

    # Need to read at least sentinel + length prefix
    header_len = len(_SENTINEL) + 4
    header_bits = header_len * 8

    if header_bits > total:
        raise ValueError("Image too small or does not contain a message")

    if generator is None:
        pos_it = _positions_sequential(header_bits, shift=shift)
    else:
        pos_it = _positions_from_generator(generator, header_bits, shift=shift)

    header_bits_list = _reveal_bits_from_channels(channels, header_bits, pos_it)
    header_bytes = bytes(bytes_from_bits(iter(header_bits_list)))

    if not header_bytes.startswith(_SENTINEL):
        raise ValueError("No hidden message found")

    length_bytes = header_bytes[len(_SENTINEL):len(_SENTINEL) + 4]
    msg_len = int.from_bytes(length_bytes, "big", signed=False)
    if msg_len < 0:
        raise ValueError("Malformed message length")

    msg_bits = msg_len * 8
    if header_bits + msg_bits > total:
        raise ValueError("Malformed message or wrong generator/shift")

    # Continue with the same iterator (already consumed header_bits positions)
    msg_bits_list = _reveal_bits_from_channels(channels, msg_bits, pos_it)
    msg_bytes = bytes(bytes_from_bits(iter(msg_bits_list)))
    return bytes_to_text(msg_bytes, encoding=encoding)