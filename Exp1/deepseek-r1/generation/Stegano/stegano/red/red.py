from PIL import Image
from ..tools.bititerator import BitIterator
from ..tools.utils import convert_image

def hide(image, message):
    image = convert_image(image)
    pixels = image.load()
    width, height = image.size
    total_pixels = width * height
    
    message_bytes = message.encode()
    bit_iterator = BitIterator(message_bytes)
    
    for y in range(height):
        for x in range(width):
            try:
                bit = next(bit_iterator)
            except StopIteration:
                return image
            r, g, b = pixels[x, y][:3]
            r = (r & 0xFE) | bit
            pixels[x, y] = (r, g, b) + pixels[x, y][3:]
    
    return image

def reveal(image):
    pixels = image.load()
    width, height = image.size
    
    bits = []
    for y in range(height):
        for x in range(width):
            r = pixels[x, y][0]
            bits.append(r & 1)
            if len(bits) % 8 == 0 and bits[-8:] == [0] * 8:
                break
        if bits[-8:] == [0] * 8:
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
    
    return bytes(byte_list).decode(errors="ignore").rstrip('\x00')