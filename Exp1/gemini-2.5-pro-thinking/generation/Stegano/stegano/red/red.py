from PIL import Image
from ..tools import utils, bititerator

def hide(image, message) -> Image.Image:
    """
    Hides a message in the red channel of an image.

    :param image: An image file path or a PIL.Image.Image object.
    :param message: The message to hide (str or bytes).
    :return: A new PIL.Image.Image object with the hidden message.
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image

    if img.mode not in ['RGB', 'RGBA']:
        img = img.convert('RGB')

    new_img = img.copy()
    pixels = new_img.load()
    width, height = new_img.size

    capacity = width * height
    message_bytes = utils.to_bytes(message, "UTF-8")
    
    if len(message_bytes) * 8 > capacity:
        raise ValueError("Message is too large for the image.")

    message_bits_iter = iter(bititerator.bits_from_bytes(message_bytes))
    pixel_coords = ((x, y) for y in range(height) for x in range(width))

    for bit in message_bits_iter:
        try:
            x, y = next(pixel_coords)
        except StopIteration:
            raise ValueError("Image capacity exceeded unexpectedly.")
    
        r, g, b, *a = pixels[x, y]
        r = (r & ~1) | bit
        
        if a:
            pixels[x, y] = (r, g, b, a[0])
        else:
            pixels[x, y] = (r, g, b)

    return new_img

def reveal(image) -> str:
    """
    Reveals a message hidden in the red channel of an image.

    :param image: An image file path or a PIL.Image.Image object.
    :return: The revealed message as a string.
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image

    pixels = img.load()
    width, height = img.size
    
    terminator_bits = utils.get_terminator_bits()
    terminator_len = len(terminator_bits)
    
    extracted_bits = []
    
    pixel_coords = ((x, y) for y in range(height) for x in range(width))

    for x, y in pixel_coords:
        r, _, _, *_ = pixels[x, y]
        lsb = r & 1
        extracted_bits.append(lsb)
        
        if len(extracted_bits) >= terminator_len:
            if extracted_bits[-terminator_len:] == terminator_bits:
                break
    else:
        raise ValueError("Terminator not found.")

    message_bits = extracted_bits[:-terminator_len]
    
    byte_array = bytearray()
    for i in range(0, len(message_bits), 8):
        byte_chunk = message_bits[i:i+8]
        if len(byte_chunk) < 8:
            break
        byte = 0
        for bit in byte_chunk:
            byte = (byte << 1) | bit
        byte_array.append(byte)
        
    return byte_array.decode("UTF-8", errors="ignore")