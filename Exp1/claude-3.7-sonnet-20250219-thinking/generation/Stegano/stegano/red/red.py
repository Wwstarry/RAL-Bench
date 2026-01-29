"""
Red channel steganography implementation.
Hides messages in the red channel of RGB images.
"""
from typing import Union
from PIL import Image

def hide(image: Union[str, Image.Image], message: str) -> Image.Image:
    """
    Hide a message in the red channel of an RGB image.
    
    Args:
        image: Path to an image or a PIL.Image instance
        message: Message to hide
        
    Returns:
        PIL.Image with the hidden message
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image.copy()
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Convert message to binary
    binary_message = ''.join(format(ord(c), '08b') for c in message)
    binary_message += '00000000'  # Add null byte to mark end of message
    
    # Check if message fits in image
    width, height = img.size
    if len(binary_message) > width * height:
        raise ValueError("Message too large for the image")
    
    pixels = list(img.getdata())
    new_pixels = []
    
    # Hide the message in the LSB of the red channel
    binary_index = 0
    for i, (r, g, b) in enumerate(pixels):
        if binary_index < len(binary_message):
            # Set the LSB of red channel to the current message bit
            r = (r & ~1) | int(binary_message[binary_index])
            binary_index += 1
        
        new_pixels.append((r, g, b))
    
    # Create a new image with the modified pixels
    steg_img = Image.new('RGB', img.size)
    steg_img.putdata(new_pixels)
    
    return steg_img

def reveal(image: Union[str, Image.Image]) -> str:
    """
    Reveal a message hidden in the red channel of an RGB image.
    
    Args:
        image: Path to an image or a PIL.Image instance
        
    Returns:
        The hidden message
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    binary_message = ""
    pixels = list(img.getdata())
    
    for r, _, _ in pixels:
        # Extract the LSB from the red channel
        binary_message += str(r & 1)
        
        # Check if we have a complete byte and if it's a null byte
        if len(binary_message) % 8 == 0:
            if len(binary_message) >= 8:
                byte = binary_message[-8:]
                if byte == '00000000':
                    binary_message = binary_message[:-8]  # Remove null byte
                    break
    
    # Convert binary string to text
    message = ""
    for i in range(0, len(binary_message), 8):
        if i + 8 <= len(binary_message):
            byte = binary_message[i:i+8]
            message += chr(int(byte, 2))
    
    return message