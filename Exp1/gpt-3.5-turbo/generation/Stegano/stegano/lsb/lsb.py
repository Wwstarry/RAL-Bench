from PIL import Image
from typing import Iterator, Optional
from ..tools.bititerator import BitIterator
from ..tools.utils import text_to_bits, bits_to_text


def hide(image: Image.Image, message: str, generator: Optional[Iterator[int]] = None, shift: int = 0,
         encoding: str = "UTF-8", auto_convert_rgb: bool = False) -> Image.Image:
    """
    Hide a message in the least significant bits of an image.

    :param image: PIL Image to hide message in
    :param message: message string to hide
    :param generator: optional generator of pixel indices to use for hiding bits
    :param shift: bit shift for LSB (0 means least significant bit)
    :param encoding: encoding for message string
    :param auto_convert_rgb: if True, convert image to RGB if not already
    :return: new PIL Image with message hidden
    """
    if image.mode not in ("RGB", "RGBA", "L"):
        if auto_convert_rgb:
            image = image.convert("RGB")
        else:
            raise ValueError("Unsupported image mode for LSB steganography: {}".format(image.mode))

    img = image.copy()
    pixels = img.load()
    width, height = img.size

    # Convert message to bits and append delimiter (null char) to mark end
    message_bytes = message.encode(encoding) + b'\x00'
    bits = text_to_bits(message_bytes)

    # Flatten pixel data indices for iteration
    # For RGB or RGBA, we hide in all channels except alpha
    channels = len(img.getbands())
    max_pixels = width * height * channels

    # Generator for pixel bit positions
    if generator is None:
        # default: sequential indices from 0 to max_pixels-1
        def default_gen():
            for i in range(max_pixels):
                yield i
        generator = default_gen()

    bit_iter = iter(bits)
    try:
        for bit in bit_iter:
            idx = next(generator) + shift
            if idx >= max_pixels:
                raise ValueError("Message too long to hide in image with given generator and shift")

            pixel_pos = idx // channels
            channel = idx % channels
            x = pixel_pos % width
            y = pixel_pos // width

            pixel = list(pixels[x, y])
            # Modify the bit at position shift in the channel
            # Clear the bit at position shift
            pixel[channel] &= ~(1 << shift)
            # Set the bit to bit value
            pixel[channel] |= (bit << shift)
            pixels[x, y] = tuple(pixel)
    except StopIteration:
        # All bits hidden
        pass

    return img


def reveal(image: Image.Image, generator: Optional[Iterator[int]] = None, shift: int = 0,
           encoding: str = "UTF-8") -> str:
    """
    Reveal a hidden message from the least significant bits of an image.

    :param image: PIL Image to reveal message from
    :param generator: optional generator of pixel indices to use for revealing bits
    :param shift: bit shift for LSB (0 means least significant bit)
    :param encoding: encoding for message string
    :return: revealed message string
    """
    if image.mode not in ("RGB", "RGBA", "L"):
        raise ValueError("Unsupported image mode for LSB steganography: {}".format(image.mode))

    pixels = image.load()
    width, height = image.size
    channels = len(image.getbands())
    max_pixels = width * height * channels

    if generator is None:
        def default_gen():
            for i in range(max_pixels):
                yield i
        generator = default_gen()

    bits = []
    for idx in generator:
        if idx >= max_pixels:
            break
        idx_shifted = idx + shift
        if idx_shifted >= max_pixels:
            break

        pixel_pos = idx_shifted // channels
        channel = idx_shifted % channels
        x = pixel_pos % width
        y = pixel_pos // width

        pixel = pixels[x, y]
        bit = (pixel[channel] >> shift) & 1
        bits.append(bit)

        # Check if we have a full byte and if it is null byte (end of message)
        if len(bits) % 8 == 0:
            byte = 0
            for b in bits[-8:]:
                byte = (byte << 1) | b
            if byte == 0:
                # Null byte found, end of message
                break

    message_bytes = bits_to_text(bits)
    # Remove trailing null byte
    if message_bytes.endswith(b'\x00'):
        message_bytes = message_bytes[:-1]
    return message_bytes.decode(encoding, errors='replace')