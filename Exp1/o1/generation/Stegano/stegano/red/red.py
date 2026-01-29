from typing import Optional
from PIL import Image
from stegano.tools.utils import (
    int_to_bytes,
    bytes_to_int,
    bytes_to_bits,
    bits_to_bytes
)


def hide(image: Image.Image, message: str) -> Image.Image:
    """
    Hide a text message using only the red channel.
    :param image: PIL Image to use as cover (RGB or RGBA ideally).
    :param message: The text message to hide.
    :return: A new PIL Image with the hidden message.
    """
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    # Encode message
    encoding = "UTF-8"
    message_bytes = message.encode(encoding)
    length_bytes = int_to_bytes(len(message_bytes), 4)
    full_data = length_bytes + message_bytes
    bits = bytes_to_bits(full_data)

    new_img = image.copy()
    px = new_img.load()
    width, height = new_img.size

    capacity = width * height
    if len(bits) > capacity:
        raise ValueError("Message too large to fit in the red channel LSBs (1 bit per pixel).")

    bit_idx = 0
    for y in range(height):
        for x in range(width):
            if bit_idx >= len(bits):
                break
            r, g, b = px[x, y][:3]
            # embed bit in red channel's LSB
            r = (r & 0xFE) | bits[bit_idx]
            bit_idx += 1
            if image.mode == "RGBA":
                a = px[x, y][3]
                px[x, y] = (r, g, b, a)
            else:
                px[x, y] = (r, g, b)
        if bit_idx >= len(bits):
            break

    return new_img


def reveal(image: Image.Image) -> str:
    """
    Reveal a hidden text message from the red channel's LSB.
    :param image: PIL Image containing hidden text (RGB or RGBA).
    :return: The hidden text.
    """
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")

    px = image.load()
    width, height = image.size

    # First read 4 bytes (32 bits) for length
    length_bits = []
    bit_count = 32
    read_bits = 0

    coords = [(x, y) for y in range(height) for x in range(width)]
    if len(coords) < bit_count:
        raise ValueError("Not enough pixels to read length info.")

    # read length
    for i in range(bit_count):
        x, y = coords[i]
        r, g, b = px[x, y][:3]
        length_bits.append(r & 1)

    length_bytes = bits_to_bytes(length_bits)
    msg_length = bytes_to_int(length_bytes)

    # now read msg_length bytes => msg_length * 8 bits
    total_bits = msg_length * 8
    if len(coords) < bit_count + total_bits:
        raise ValueError("Not enough pixels to read the entire message.")

    msg_bits = []
    for i in range(bit_count, bit_count + total_bits):
        x, y = coords[i]
        r, g, b = px[x, y][:3]
        msg_bits.append(r & 1)

    hidden_bytes = bits_to_bytes(msg_bits)
    return hidden_bytes.decode("UTF-8")