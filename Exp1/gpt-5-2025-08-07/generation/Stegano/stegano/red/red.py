from typing import List, Tuple, Union
from PIL import Image
from ..tools.utils import (
    ensure_image_mode,
    message_to_bytes,
    int_to_bits_be,
    bytes_to_bits,
    bits_to_int_be,
    bits_to_bytes,
    image_pixels_as_tuples,
    put_pixels_from_tuples,
)

def hide(image: Image.Image, message: Union[str, bytes]) -> Image.Image:
    """
    Hide text in the red channel (LSB) of an RGB/RGBA image.
    Stores a 32-bit big-endian length prefix followed by message bytes.
    """
    if not isinstance(image, Image.Image):
        raise TypeError("image must be a PIL.Image.Image instance")
    img = ensure_image_mode(image, auto_convert_rgb=True)  # ensure we have RGB channels available

    msg_bytes = message_to_bytes(message, "UTF-8")
    payload_bits = bytes_to_bits(msg_bytes)
    length_bits = int_to_bits_be(len(msg_bytes), 32)
    full_bits = length_bits + payload_bits

    pixels = image_pixels_as_tuples(img)
    # Use only red channel (index 0 in RGB/RGBA). If grayscale ('L'), fallback to that single channel.
    bands = img.getbands()
    if "R" in bands:
        red_index = bands.index("R")
    else:
        # Fallback: single channel mode (L/LA)
        red_index = 0

    capacity = len(pixels)
    if len(full_bits) > capacity:
        raise ValueError("Not enough capacity in red channel to hide the message.")

    mutable_pixels: List[List[int]] = [list(p) for p in pixels]
    for i, bit in enumerate(full_bits):
        original_value = mutable_pixels[i][red_index]
        mutable_pixels[i][red_index] = (original_value & ~1) | (bit & 1)

    new_img = img.copy()
    new_pixels_tuples: List[Tuple[int, ...]] = [tuple(p) for p in mutable_pixels]
    put_pixels_from_tuples(new_img, new_pixels_tuples)
    return new_img

def reveal(image: Image.Image) -> str:
    """
    Reveal a message hidden in the red channel LSBs using the 32-bit length header.
    """
    if not isinstance(image, Image.Image):
        raise TypeError("image must be a PIL.Image.Image instance")
    img = ensure_image_mode(image, auto_convert_rgb=True)

    pixels = image_pixels_as_tuples(img)
    bands = img.getbands()
    red_index = bands.index("R") if "R" in bands else 0

    # Read 32 bits length header
    length_bits: List[int] = []
    for i in range(32):
        length_bits.append(pixels[i][red_index] & 1)
    msg_len = bits_to_int_be(length_bits)

    payload_bits_count = msg_len * 8
    payload_bits: List[int] = []
    start = 32
    end = start + payload_bits_count
    if end > len(pixels):
        raise ValueError("Not enough data to reveal the message from red channel.")
    for i in range(start, end):
        payload_bits.append(pixels[i][red_index] & 1)
    msg_bytes = bits_to_bytes(payload_bits)
    try:
        return msg_bytes.decode("UTF-8", errors="strict")
    except Exception:
        return msg_bytes.decode("UTF-8", errors="replace")