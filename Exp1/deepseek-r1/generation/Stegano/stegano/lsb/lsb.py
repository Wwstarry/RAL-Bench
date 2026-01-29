from PIL import Image
import itertools
from ..tools.bititerator import BitIterator
from ..tools.utils import convert_image, get_image_pixel_count

def hide(image, message, generator=None, shift=0, encoding="UTF-8", auto_convert_rgb=False):
    if auto_convert_rgb:
        image = convert_image(image)
    pixels = image.load()
    width, height = image.size
    total_pixels = width * height
    
    message_bytes = message.encode(encoding)
    bit_iterator = BitIterator(message_bytes)
    
    if generator is None:
        indices = itertools.product(range(width), range(height))
    else:
        indices = ((index % width, index // width) for index in generator)
    
    for idx, (x, y) in enumerate(indices):
        if idx < shift:
            continue
        try:
            bit = next(bit_iterator)
        except StopIteration:
            break
        r, g, b = pixels[x, y][:3]
        r = (r & 0xFE) | bit
        pixels[x, y] = (r, g, b) + pixels[x, y][3:]
    
    return image

def reveal(image, generator=None, shift=0, encoding="UTF-8"):
    pixels = image.load()
    width, height = image.size
    
    if generator is None:
        indices = itertools.product(range(width), range(height))
    else:
        indices = ((index % width, index // width) for index in generator)
    
    bits = []
    for idx, (x, y) in enumerate(indices):
        if idx < shift:
            continue
        r = pixels[x, y][0]
        bits.append(r & 1)
        if len(bits) % 8 == 0 and bits[-8:] == [0] * 8:
            break
    
    byte_list = []
    for i in range(0, len(bits) - 7, 8):
        byte = bits[i:i+8]
        if byte == [0] * 8:
            break
        byte_value = 0
        for bit in byte:
            byte_value = (byte_value << 1) | bit
        byte_list.append(byte_value)
    
    return bytes(byte_list).decode(encoding, errors="ignore").rstrip('\x00')