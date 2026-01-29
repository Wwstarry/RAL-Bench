"""
Red channel implementation for hiding and revealing messages
"""
from PIL import Image
from typing import Union
from ..tools.bititerator import BitIterator


def hide(image: Union[str, Image.Image], message: str) -> Image.Image:
    """
    Hide a message in the red channel of an RGB image
    
    Args:
        image: Input image path or PIL Image object
        message: Message to hide
    
    Returns:
        PIL Image with hidden message
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image.copy()
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Convert message to bytes
    message_bytes = message.encode('UTF-8')
    bits = BitIterator(message_bytes)
    
    pixels = img.load()
    width, height = img.size
    
    # Hide bits in red channel LSB
    for y in range(height):
        for x in range(width):
            if not bits.has_next():
                break
            
            r, g, b = pixels[x, y]
            bit = bits.next()
            r = (r & ~1) | bit
            pixels[x, y] = (r, g, b)
        
        if not bits.has_next():
            break
    
    if bits.has_next():
        raise ValueError("Image too small to hide message")
    
    return img


def reveal(image: Union[str, Image.Image]) -> str:
    """
    Reveal a hidden message from the red channel of an RGB image
    
    Args:
        image: Input image path or PIL Image object
    
    Returns:
        Revealed message string
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    pixels = img.load()
    width, height = img.size
    
    # Extract bits from red channel LSB
    collected_bits = []
    byte_buffer = 0
    bit_count = 0
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            bit = r & 1
            byte_buffer = (byte_buffer << 1) | bit
            bit_count += 1
            
            if bit_count == 8:
                collected_bits.append(byte_buffer)
                byte_buffer = 0
                bit_count = 0
                
                # Check for termination (8 zero bytes)
                if len(collected_bits) >= 8:
                    if all(b == 0 for b in collected_bits[-8:]):
                        collected_bits = collected_bits[:-8]
                        return bytes(collected_bits).decode('UTF-8')
    
    # If we get here, try to decode what we have
    return bytes(collected_bits).decode('UTF-8', errors='ignore')