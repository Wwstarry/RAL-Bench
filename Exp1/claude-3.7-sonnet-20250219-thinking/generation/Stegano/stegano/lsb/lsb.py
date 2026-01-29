"""
LSB steganography implementation.
Hides and reveals messages in the least significant bits of an image.
"""
import sys
from typing import Iterator, Optional, Union
from PIL import Image

def hide(
    image: Union[str, Image.Image],
    message: str,
    generator: Optional[Iterator[int]] = None,
    shift: int = 0,
    encoding: str = "UTF-8",
    auto_convert_rgb: bool = False
) -> Image.Image:
    """
    Hide a message in an image using LSB steganography.
    
    Args:
        image: Path to an image or a PIL.Image instance
        message: Message to hide
        generator: Generator function to determine pixel selection pattern
        shift: Shift value for the generator
        encoding: Character encoding for the message
        auto_convert_rgb: Convert image to RGB if needed
        
    Returns:
        PIL.Image with the hidden message
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image.copy()
    
    if auto_convert_rgb and img.mode != 'RGB':
        img = img.convert('RGB')
    
    if img.mode not in ['RGB', 'RGBA']:
        raise ValueError(f"Unsupported image mode: {img.mode}. Use RGB or RGBA images.")
    
    width, height = img.size
    max_pixels = width * height
    
    message_bytes = (message + '\0').encode(encoding)
    message_bits = ''.join([bin(byte)[2:].zfill(8) for byte in message_bytes])
    
    if len(message_bits) > max_pixels * 3:
        raise ValueError("Message too large for the image")
    
    pixels = list(img.getdata())
    new_pixels = []
    
    if generator is None:
        # Use a simple sequential generator if none provided
        def sequential():
            n = 0
            while True:
                yield n
                n += 1
        generator = sequential()
    
    # Skip the first 'shift' pixels
    for _ in range(shift):
        next(generator)
    
    pixel_indices = []
    for _ in range(len(message_bits)):
        pixel_indices.append(next(generator) % max_pixels)
    
    pixel_mapping = {}
    for i, idx in enumerate(pixel_indices):
        if idx not in pixel_mapping:
            pixel_mapping[idx] = []
        if len(pixel_mapping[idx]) < 3:  # We can use up to 3 channels (RGB)
            pixel_mapping[idx].append(i)
    
    message_bit_index = 0
    for i, pixel in enumerate(pixels):
        if i in pixel_mapping:
            channels = list(pixel)
            for channel_idx in pixel_mapping[i]:
                if message_bit_index < len(message_bits):
                    # Modify the LSB of this channel
                    channels[channel_idx % 3] = (channels[channel_idx % 3] & ~1) | int(message_bits[message_bit_index])
                    message_bit_index += 1
            new_pixels.append(tuple(channels))
        else:
            new_pixels.append(pixel)
    
    # Create a new image with the modified pixels
    steg_img = Image.new(img.mode, img.size)
    steg_img.putdata(new_pixels)
    
    return steg_img

def reveal(
    image: Union[str, Image.Image],
    generator: Optional[Iterator[int]] = None,
    shift: int = 0,
    encoding: str = "UTF-8"
) -> str:
    """
    Reveal a message hidden in an image using LSB steganography.
    
    Args:
        image: Path to an image or a PIL.Image instance
        generator: Generator function to determine pixel selection pattern
        shift: Shift value for the generator
        encoding: Character encoding for the message
        
    Returns:
        The hidden message
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image
    
    if img.mode not in ['RGB', 'RGBA']:
        raise ValueError(f"Unsupported image mode: {img.mode}. Use RGB or RGBA images.")
    
    width, height = img.size
    max_pixels = width * height
    pixels = list(img.getdata())
    
    if generator is None:
        # Use a simple sequential generator if none provided
        def sequential():
            n = 0
            while True:
                yield n
                n += 1
        generator = sequential()
    
    # Skip the first 'shift' pixels
    for _ in range(shift):
        next(generator)
    
    binary_message = ""
    null_byte_found = False
    
    # Extract bits until we find a null byte or reach the end of the image
    while not null_byte_found and len(binary_message) < max_pixels * 3:
        pixel_index = next(generator) % max_pixels
        pixel = pixels[pixel_index]
        
        for i in range(min(3, len(pixel))):  # Up to 3 channels (RGB)
            binary_message += str(pixel[i] & 1)
            
            # Check if we have enough bits to form a byte
            if len(binary_message) % 8 == 0:
                # Check if we've found a null byte
                if len(binary_message) >= 8:
                    byte = int(binary_message[-8:], 2)
                    if byte == 0:
                        null_byte_found = True
                        break
        
        if null_byte_found:
            break
    
    # Convert binary string to bytes
    message_bytes = bytearray()
    for i in range(0, len(binary_message) - len(binary_message) % 8, 8):
        byte = int(binary_message[i:i+8], 2)
        if byte == 0:  # Stop at null byte
            break
        message_bytes.append(byte)
    
    # Convert bytes to string
    try:
        return message_bytes.decode(encoding)
    except UnicodeDecodeError:
        return message_bytes.decode(encoding, errors="replace")