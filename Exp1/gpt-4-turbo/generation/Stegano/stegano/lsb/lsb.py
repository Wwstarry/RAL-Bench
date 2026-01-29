from PIL import Image
from stegano.tools.bititerator import BitIterator
from stegano.lsb.generators import eratosthenes

def _message_to_bits(message, encoding="UTF-8"):
    if isinstance(message, str):
        message_bytes = message.encode(encoding)
    else:
        message_bytes = message
    # Add a null byte as a terminator
    message_bytes += b'\x00'
    for byte in message_bytes:
        for i in range(8):
            yield (byte >> (7 - i)) & 1

def _bits_to_message(bits, encoding="UTF-8"):
    bytes_out = bytearray()
    byte = 0
    count = 0
    for bit in bits:
        byte = (byte << 1) | bit
        count += 1
        if count == 8:
            if byte == 0:
                break
            bytes_out.append(byte)
            byte = 0
            count = 0
    return bytes_out.decode(encoding)

def hide(image, message, generator=None, shift=0, encoding="UTF-8", auto_convert_rgb=False):
    if isinstance(image, str):
        image = Image.open(image)
    if auto_convert_rgb and image.mode != "RGB":
        image = image.convert("RGB")
    elif image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    pixels = image.load()
    width, height = image.size
    bits = list(_message_to_bits(message, encoding))
    if generator is None:
        positions = ((x, y) for y in range(height) for x in range(width))
    else:
        gen = generator()
        positions = ((i % width, i // width) for i in gen)
    idx = 0
    for pos in positions:
        if idx >= len(bits):
            break
        x, y = pos
        if y >= height:
            break
        pixel = list(pixels[x, y])
        pixel[shift] = (pixel[shift] & ~1) | bits[idx]
        pixels[x, y] = tuple(pixel)
        idx += 1
    return image

def reveal(image, generator=None, shift=0, encoding="UTF-8"):
    if isinstance(image, str):
        image = Image.open(image)
    if image.mode not in ("RGB", "RGBA"):
        image = image.convert("RGB")
    pixels = image.load()
    width, height = image.size
    if generator is None:
        positions = ((x, y) for y in range(height) for x in range(width))
    else:
        gen = generator()
        positions = ((i % width, i // width) for i in gen)
    bits = []
    for pos in positions:
        x, y = pos
        if y >= height:
            break
        pixel = pixels[x, y]
        bits.append((pixel[shift] & 1))
        if len(bits) % 8 == 0 and bits[-8:] == [0]*8:
            break
    return _bits_to_message(bits, encoding)