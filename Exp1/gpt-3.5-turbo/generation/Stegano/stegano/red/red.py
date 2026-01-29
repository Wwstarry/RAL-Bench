from PIL import Image


def hide(image: Image.Image, message: str) -> Image.Image:
    """
    Hide a message in the red channel of an RGB image using LSB steganography.

    :param image: PIL Image (must be RGB)
    :param message: message string to hide
    :return: new PIL Image with message hidden
    """
    if image.mode != "RGB":
        raise ValueError("Image must be in RGB mode for red channel steganography")

    img = image.copy()
    pixels = img.load()
    width, height = img.size

    message_bytes = message.encode("UTF-8") + b'\x00'
    bits = []
    for byte in message_bytes:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)

    max_bits = width * height
    if len(bits) > max_bits:
        raise ValueError("Message too long to hide in image")

    bit_idx = 0
    for y in range(height):
        for x in range(width):
            if bit_idx >= len(bits):
                break
            r, g, b = pixels[x, y]
            r = (r & 0xFE) | bits[bit_idx]
            pixels[x, y] = (r, g, b)
            bit_idx += 1
        if bit_idx >= len(bits):
            break

    return img


def reveal(image: Image.Image) -> str:
    """
    Reveal a hidden message from the red channel of an RGB image.

    :param image: PIL Image (must be RGB)
    :return: revealed message string
    """
    if image.mode != "RGB":
        raise ValueError("Image must be in RGB mode for red channel steganography")

    pixels = image.load()
    width, height = image.size

    bits = []
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            bits.append(r & 1)

    bytes_out = bytearray()
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i + 8]
        if len(byte_bits) < 8:
            break
        byte = 0
        for bit in byte_bits:
            byte = (byte << 1) | bit
        if byte == 0:
            break
        bytes_out.append(byte)

    return bytes_out.decode("UTF-8", errors='replace')