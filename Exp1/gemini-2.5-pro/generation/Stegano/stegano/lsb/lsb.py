# stegano/lsb/lsb.py
from PIL import Image
import itertools

from stegano.tools import utils

def _get_pixel_generator(img, generator=None, shift=0):
    """
    Returns a generator for pixel coordinates (x, y).
    If a generator is provided, it yields indices which are then converted to (x, y).
    Otherwise, it yields sequential (x, y) coordinates.
    """
    width, height = img.size
    max_pixels = width * height

    if generator:
        # Use the provided prime number generator
        # Skip 'shift' number of primes
        gen = itertools.islice(generator(), shift, None)
        for i in gen:
            if i < max_pixels:
                yield (i % width, i // width)
            else:
                # The generator produced an index out of bounds.
                break
    else:
        # Sequential generator
        for i in range(max_pixels):
            yield (i % width, i // width)

def hide(image, message, generator=None, shift=0, encoding="UTF-8", auto_convert_rgb=False):
    """
    Hides a message in the LSB of an image.
    """
    if not isinstance(image, Image.Image):
        try:
            img = Image.open(image)
        except Exception as e:
            raise TypeError("The 'image' parameter must be a PIL.Image.Image object or a file path.") from e
    else:
        img = image

    if img.mode != 'RGB' and auto_convert_rgb:
        img = img.convert('RGB')
    elif img.mode not in ['RGB', 'RGBA']:
        raise ValueError("Steganography is only supported for RGB or RGBA images.")

    new_img = img.copy()
    pixels = new_img.load()

    message_bits = utils.get_bit_generator(message, encoding)
    pixel_gen = _get_pixel_generator(new_img, generator, shift)
    
    try:
        for x, y in pixel_gen:
            pixel = list(pixels[x, y])
            for i in range(3): # R, G, B channels
                try:
                    bit = next(message_bits)
                    pixel[i] = (pixel[i] & 0xFE) | bit
                except StopIteration:
                    # No more bits to hide
                    pixels[x, y] = tuple(pixel)
                    return new_img
            pixels[x, y] = tuple(pixel)
    except Exception as e:
        raise ValueError("The message is too long to be hidden in the image.") from e

    # If we are here, it means the pixel generator was exhausted before the message was fully hidden.
    raise ValueError("The message is too long to be hidden in the image.")


def reveal(image, generator=None, shift=0, encoding="UTF-8"):
    """
    Reveals a message hidden in the LSB of an image.
    """
    if not isinstance(image, Image.Image):
        try:
            img = Image.open(image)
        except Exception as e:
            raise TypeError("The 'image' parameter must be a PIL.Image.Image object or a file path.") from e
    else:
        img = image

    if img.mode not in ['RGB', 'RGBA']:
        raise ValueError("Steganography is only supported for RGB or RGBA images.")

    pixels = img.load()
    pixel_gen = _get_pixel_generator(img, generator, shift)
    
    extracted_bits = []
    delimiter_found = False

    for x, y in pixel_gen:
        pixel = pixels[x, y]
        for i in range(3): # R, G, B channels
            extracted_bits.append(pixel[i] & 1)
            if len(extracted_bits) >= 8 and extracted_bits[-8:] == utils.DELIMITER:
                delimiter_found = True
                break
        if delimiter_found:
            break
    
    if not delimiter_found:
        raise ValueError("No hidden message found or delimiter is missing.")

    # Remove the delimiter
    message_bits = extracted_bits[:-8]
    
    try:
        message_bytes = utils.bits_to_bytes(message_bits)
        return message_bytes.decode(encoding)
    except UnicodeDecodeError as e:
        raise ValueError("Failed to decode message. The encoding might be incorrect.") from e
    except ValueError as e:
        # This can happen if bits_to_bytes gets a non-multiple of 8 length
        raise ValueError("Failed to reconstruct message from bits. Data may be corrupt.") from e