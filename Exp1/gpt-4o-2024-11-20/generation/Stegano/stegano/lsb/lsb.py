from PIL import Image
from stegano.lsb.generators import eratosthenes

def hide(image, message, generator=None, shift=0, encoding="UTF-8", auto_convert_rgb=False):
    if auto_convert_rgb and image.mode != "RGB":
        image = image.convert("RGB")
    pixels = list(image.getdata())
    binary_message = ''.join(format(ord(char), '08b') for char in message.encode(encoding)) + '00000000'
    generator = generator or range(len(pixels))
    for index in generator:
        if index >= len(binary_message):
            break
        pixel = list(pixels[index])
        pixel[shift] = (pixel[shift] & ~1) | int(binary_message[index])
        pixels[index] = tuple(pixel)
    new_image = Image.new(image.mode, image.size)
    new_image.putdata(pixels)
    return new_image

def reveal(image, generator=None, shift=0, encoding="UTF-8"):
    pixels = list(image.getdata())
    generator = generator or range(len(pixels))
    binary_message = ""
    for index in generator:
        binary_message += str(pixels[index][shift] & 1)
    byte_message = [binary_message[i:i+8] for i in range(0, len(binary_message), 8)]
    decoded_message = ''.join(chr(int(byte, 2)) for byte in byte_message if int(byte, 2) != 0)
    return decoded_message