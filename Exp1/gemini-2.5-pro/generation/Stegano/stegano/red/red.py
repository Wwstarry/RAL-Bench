# stegano/red/red.py
from PIL import Image

from stegano.tools import utils

def hide(image, message):
    """
    Hides a message in the LSB of the red channel of an image.
    """
    encoding = "UTF-8" # Default encoding
    if not isinstance(image, Image.Image):
        try:
            img = Image.open(image)
        except Exception as e:
            raise TypeError("The 'image' parameter must be a PIL.Image.Image object or a file path.") from e
    else:
        img = image

    if img.mode not in ['RGB', 'RGBA']:
        img = img.convert('RGB')

    new_img = img.copy()
    pixels = new_img.load()
    width, height = new_img.size

    message_bits = utils.get_bit_generator(message, encoding)
    
    try:
        for y in range(height):
            for x in range(width):
                pixel = list(pixels[x, y])
                try:
                    bit = next(message_bits)
                    pixel[0] = (pixel[0] & 0xFE) | bit
                    pixels[x, y] = tuple(pixel)
                except StopIteration:
                    # All bits hidden
                    return new_img
    except IndexError:
        raise ValueError("Image mode must be RGB or RGBA.")

    raise ValueError("The message is too long to be hidden in the image.")


def reveal(image):
    """
    Reveals a message hidden in the LSB of the red channel of an image.
    """
    encoding = "UTF-8" # Default encoding
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
    width, height = img.size
    
    extracted_bits = []
    delimiter_found = False

    for y in range(height):
        for x in range(width):
            pixel = pixels[x, y]
            extracted_bits.append(pixel[0] & 1)
            
            if len(extracted_bits) >= 8 and extracted_bits[-8:] == utils.DELIMITER:
                delimiter_found = True
                break
        if delimiter_found:
            break
            
    if not delimiter_found:
        raise ValueError("No hidden message found or delimiter is missing.")

    message_bits = extracted_bits[:-8]
    
    try:
        message_bytes = utils.bits_to_bytes(message_bits)
        return message_bytes.decode(encoding)
    except Exception as e:
        raise ValueError("Failed to decode message. Data may be corrupt or encoding incorrect.") from e