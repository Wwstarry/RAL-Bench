import math
from typing import Optional, Iterator
from PIL import Image
from stegano.lsb.generators import eratosthenes
from stegano.tools.utils import (
    int_to_bytes,
    bytes_to_int,
    bytes_to_bits,
    bits_to_bytes
)


def hide(
    image: Image.Image,
    message: str,
    generator: Optional[Iterator[int]] = None,
    shift: int = 0,
    encoding: str = "UTF-8",
    auto_convert_rgb: bool = False
) -> Image.Image:
    """
    Hide a text message in the image using LSB steganography.
    :param image: PIL Image to use as cover.
    :param message: The text message to hide.
    :param generator: Iterator of pixel indices to use for hiding bits (default: consecutive).
    :param shift: Number of LSB positions to skip from the start (default 0).
    :param encoding: Text encoding for the message (default: UTF-8).
    :param auto_convert_rgb: If True and image is not 'RGB', convert it.
    :return: A new PIL Image with the hidden message.
    """
    if auto_convert_rgb and image.mode != "RGB":
        image = image.convert("RGB")
    elif image.mode not in ("RGB", "RGBA"):
        raise ValueError("Unsupported image mode for LSB. Use RGB or RGBA or enable auto_convert_rgb.")

    # Encode message
    message_bytes = message.encode(encoding)
    # We'll store length (4 bytes) + message bytes
    length_bytes = int_to_bytes(len(message_bytes), 4)
    full_data = length_bytes + message_bytes
    data_bits = bytes_to_bits(full_data)

    # Prepare generator
    if generator is None:
        # Default: consecutive pixel indexes
        def default_generator():
            idx = 0
            while True:
                yield idx
                idx += 1

        generator = default_generator()

    # Apply shift: skip first N items from generator
    for _ in range(shift):
        next(generator)

    # Get pixel data
    pixels = image.load()
    width, height = image.size

    # We'll hide bits in R, G, B channels (ignoring alpha if present)
    # Maximum capacity = width * height * 3 bits for RGB
    if len(data_bits) > width * height * 3:
        raise ValueError("Message too large to fit in image.")

    # We'll create a new image so as not to modify the original in place
    new_image = image.copy()
    pixels_new = new_image.load()

    bit_index = 0
    for bit in data_bits:
        idx = next(generator)
        if idx >= width * height:
            raise ValueError("Ran out of pixels to hide data.")
        x = idx % width
        y = idx // width

        r, g, b = pixels_new[x, y][:3]
        # We'll embed next bit in R
        if bit_index % 3 == 0:
            # modify LSB of r
            r = (r & 0xFE) | bit
        elif bit_index % 3 == 1:
            # modify LSB of g
            g = (g & 0xFE) | bit
        else:
            # modify LSB of b
            b = (b & 0xFE) | bit

        if image.mode == "RGBA":
            a = pixels_new[x, y][3]
            pixels_new[x, y] = (r, g, b, a)
        else:
            pixels_new[x, y] = (r, g, b)
        bit_index += 1
        if bit_index >= len(data_bits):
            break

    return new_image


def reveal(
    image: Image.Image,
    generator: Optional[Iterator[int]] = None,
    shift: int = 0,
    encoding: str = "UTF-8"
) -> str:
    """
    Reveal text hidden in the image via LSB steganography.
    :param image: PIL Image containing a hidden message.
    :param generator: Iterator of pixel indices to use for reading bits (default: consecutive).
    :param shift: Number of LSB positions to skip from the start (default 0).
    :param encoding: Text encoding for the output (default: UTF-8).
    :return: The hidden text.
    """
    if image.mode not in ("RGB", "RGBA"):
        raise ValueError("Unsupported image mode for LSB reveal. Use RGB or RGBA.")

    # Prepare generator
    if generator is None:
        # Default: consecutive pixel indexes
        def default_generator():
            idx = 0
            while True:
                yield idx
                idx += 1

        generator = default_generator()

    # Apply shift
    for _ in range(shift):
        next(generator)

    pixels = image.load()
    width, height = image.size

    # First read length (4 bytes -> 32 bits)
    length_bits = []
    for i in range(32):
        idx = next(generator)
        if idx >= width * height:
            raise ValueError("Ran out of pixels while reading message length.")
        x = idx % width
        y = idx // width
        r, g, b = pixels[x, y][:3]
        # Depending on remainder of i mod 3
        if i % 3 == 0:
            length_bits.append(r & 1)
        elif i % 3 == 1:
            length_bits.append(g & 1)
        else:
            length_bits.append(b & 1)
    length_bytes = bits_to_bytes(length_bits)
    msg_length = bytes_to_int(length_bytes)

    # Now read msg_length bytes worth of bits
    msg_bits = []
    total_bits_to_read = msg_length * 8
    for i in range(total_bits_to_read):
        idx = next(generator)
        if idx >= width * height:
            raise ValueError("Ran out of pixels while reading message.")
        x = idx % width
        y = idx // width
        r, g, b = pixels[x, y][:3]
        # Depending on remainder of i mod 3
        if i % 3 == 0:
            msg_bits.append(r & 1)
        elif i % 3 == 1:
            msg_bits.append(g & 1)
        else:
            msg_bits.append(b & 1)

    hidden_bytes = bits_to_bytes(msg_bits)
    return hidden_bytes.decode(encoding)