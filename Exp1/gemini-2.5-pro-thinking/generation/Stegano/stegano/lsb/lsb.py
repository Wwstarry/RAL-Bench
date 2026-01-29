import itertools
from PIL import Image
from ..tools import utils, bititerator

def _get_coords(img, generator=None, shift=0):
    """
    Generates pixel coordinates (x, y, channel_index) for embedding data.
    """
    width, height = img.size
    
    if img.mode == 'RGB':
        num_channels = 3
    elif img.mode == 'RGBA':
        num_channels = 4
    elif img.mode == 'L':
        num_channels = 1
    else:
        raise ValueError(f"Unsupported image mode: {img.mode}")

    total_positions = width * height * num_channels

    if generator:
        indices = itertools.islice(generator(), shift, None)
    else:
        indices = range(shift, total_positions)

    for i in indices:
        if i >= total_positions:
            continue
        
        pixel_index = i // num_channels
        channel_index = i % num_channels
        
        x = pixel_index % width
        y = pixel_index // width
        
        yield (x, y, channel_index)

def hide(image, message, generator=None, shift=0, encoding="UTF-8", auto_convert_rgb=False) -> Image.Image:
    """
    Hides a message in an image using the LSB technique.

    :param image: An image file path or a PIL.Image.Image object.
    :param message: The message to hide (str or bytes).
    :param generator: A generator for the pixel sequence.
    :param shift: The number of pixels to skip at the beginning.
    :param encoding: The encoding for the message string.
    :param auto_convert_rgb: Automatically convert the image to RGB if needed.
    :return: A new PIL.Image.Image object with the hidden message.
    """
    if isinstance(image, str):
        try:
            img = Image.open(image)
        except FileNotFoundError:
            raise
    else:
        img = image

    if auto_convert_rgb and img.mode != 'RGB':
        img = img.convert('RGB')

    new_img = img.copy()
    pixels = new_img.load()
    width, height = new_img.size

    if new_img.mode == 'RGB':
        num_channels = 3
    elif new_img.mode == 'RGBA':
        num_channels = 4
    elif new_img.mode == 'L':
        num_channels = 1
    else:
        raise ValueError(f"Unsupported image mode for hiding: {new_img.mode}")

    capacity = width * height * num_channels
    message_bytes = utils.to_bytes(message, encoding)
    
    if len(message_bytes) * 8 > capacity - (shift * 8 if not generator else 0):
        raise ValueError("Message is too large to be hidden in the image.")

    message_bits = bititerator.bits_from_bytes(message_bytes)
    coord_generator = _get_coords(new_img, generator, shift)

    try:
        for bit in message_bits:
            x, y, channel_index = next(coord_generator)
            
            pixel_val = pixels[x, y]
            pixel = list(pixel_val) if isinstance(pixel_val, tuple) else [pixel_val]
            
            pixel[channel_index] = (pixel[channel_index] & ~1) | bit
            
            pixels[x, y] = tuple(pixel) if len(pixel) > 1 else pixel[0]
    except StopIteration:
        raise ValueError("Message is too large for the given generator sequence.")

    return new_img

def reveal(image, generator=None, shift=0, encoding="UTF-8") -> str:
    """
    Reveals a message hidden in an image.

    :param image: An image file path or a PIL.Image.Image object.
    :param generator: The same generator used for hiding.
    :param shift: The same shift value used for hiding.
    :param encoding: The encoding of the hidden message.
    :return: The revealed message as a string.
    """
    if isinstance(image, str):
        try:
            img = Image.open(image)
        except FileNotFoundError:
            raise
    else:
        img = image

    pixels = img.load()
    coord_generator = _get_coords(img, generator, shift)
    
    terminator_bits = utils.get_terminator_bits()
    terminator_len = len(terminator_bits)
    
    extracted_bits = []
    
    for x, y, channel_index in coord_generator:
        pixel_val = pixels[x, y]
        pixel = list(pixel_val) if isinstance(pixel_val, tuple) else [pixel_val]
            
        lsb = pixel[channel_index] & 1
        extracted_bits.append(lsb)
        
        if len(extracted_bits) >= terminator_len:
            if extracted_bits[-terminator_len:] == terminator_bits:
                break
    else:
        raise ValueError("Terminator not found. No message hidden or message is corrupted.")

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
        
    try:
        return byte_array.decode(encoding)
    except UnicodeDecodeError:
        raise ValueError("Failed to decode message with the specified encoding.")