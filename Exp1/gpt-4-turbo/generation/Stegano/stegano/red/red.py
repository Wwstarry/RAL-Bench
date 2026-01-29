from PIL import Image

def _message_to_bits(message):
    if isinstance(message, str):
        message_bytes = message.encode("UTF-8")
    else:
        message_bytes = message
    message_bytes += b'\x00'
    for byte in message_bytes:
        for i in range(8):
            yield (byte >> (7 - i)) & 1

def _bits_to_message(bits):
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
    return bytes_out.decode("UTF-8")

def hide(image, message):
    if isinstance(image, str):
        image = Image.open(image)
    if image.mode != "RGB":
        image = image.convert("RGB")
    pixels = image.load()
    width, height = image.size
    bits = list(_message_to_bits(message))
    idx = 0
    for y in range(height):
        for x in range(width):
            if idx >= len(bits):
                break
            r, g, b = pixels[x, y]
            r = (r & ~1) | bits[idx]
            pixels[x, y] = (r, g, b)
            idx += 1
        if idx >= len(bits):
            break
    return image

def reveal(image):
    if isinstance(image, str):
        image = Image.open(image)
    if image.mode != "RGB":
        image = image.convert("RGB")
    pixels = image.load()
    width, height = image.size
    bits = []
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            bits.append(r & 1)
            if len(bits) % 8 == 0 and bits[-8:] == [0]*8:
                break
        if len(bits) % 8 == 0 and bits[-8:] == [0]*8:
            break
    return _bits_to_message(bits)