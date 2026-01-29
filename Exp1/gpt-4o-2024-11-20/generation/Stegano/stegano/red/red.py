from PIL import Image

def hide(image, message):
    pixels = list(image.getdata())
    binary_message = ''.join(format(ord(char), '08b') for char in message) + '00000000'
    for i, char in enumerate(binary_message):
        if i >= len(pixels):
            break
        pixel = list(pixels[i])
        pixel[0] = (pixel[0] & ~1) | int(char)
        pixels[i] = tuple(pixel)
    new_image = Image.new(image.mode, image.size)
    new_image.putdata(pixels)
    return new_image

def reveal(image):
    pixels = list(image.getdata())
    binary_message = ""
    for pixel in pixels:
        binary_message += str(pixel[0] & 1)
    byte_message = [binary_message[i:i+8] for i in range(0, len(binary_message), 8)]
    decoded_message = ''.join(chr(int(byte, 2)) for byte in byte_message if int(byte, 2) != 0)
    return decoded_message