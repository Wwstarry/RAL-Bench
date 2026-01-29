"""
LSB steganography implementation
"""

from PIL import Image
import io
from .generators import eratosthenes


def hide(image, message, generator=None, shift=0, encoding="UTF-8", auto_convert_rgb=False):
    """
    Hide a message in an image using LSB steganography.
    
    Args:
        image: PIL Image or path to image file
        message: String message to hide
        generator: Optional generator for pixel selection (default: sequential)
        shift: Bit shift for LSB position (default: 0)
        encoding: Text encoding (default: "UTF-8")
        auto_convert_rgb: Convert image to RGB if needed (default: False)
    
    Returns:
        PIL Image with hidden message
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image.copy()
    
    if auto_convert_rgb and img.mode != 'RGB':
        img = img.convert('RGB')
    
    if img.mode not in ('RGB', 'RGBA'):
        raise ValueError(f"Unsupported image mode: {img.mode}")
    
    # Encode message
    message_bytes = message.encode(encoding)
    message_bits = _bytes_to_bits(message_bytes)
    
    # Add length header (32 bits for message length)
    length = len(message_bytes)
    length_bits = _int_to_bits(length, 32)
    all_bits = length_bits + message_bits
    
    # Get pixel data
    pixels = img.load()
    width, height = img.size
    
    # Determine which pixels to use
    if generator is None:
        pixel_indices = range(width * height)
    else:
        pixel_indices = generator()
    
    bit_index = 0
    pixel_count = 0
    
    for pixel_idx in pixel_indices:
        if bit_index >= len(all_bits):
            break
        
        row = pixel_idx // width
        col = pixel_idx % width
        
        if row >= height:
            break
        
        pixel = pixels[col, row]
        
        if isinstance(pixel, int):
            # Grayscale
            pixel = (pixel, pixel, pixel)
        elif not isinstance(pixel, tuple):
            pixel = tuple(pixel)
        
        # Modify pixel with message bits
        new_pixel = list(pixel)
        
        for channel in range(min(len(new_pixel), 3)):
            if bit_index >= len(all_bits):
                break
            
            bit = all_bits[bit_index]
            bit_index += 1
            
            # Clear LSB and set new bit
            new_pixel[channel] = (new_pixel[channel] & ~(1 << shift)) | (bit << shift)
        
        if len(new_pixel) == 4:
            pixels[col, row] = tuple(new_pixel)
        else:
            pixels[col, row] = tuple(new_pixel[:3])
        
        pixel_count += 1
    
    return img


def reveal(image, generator=None, shift=0, encoding="UTF-8"):
    """
    Reveal a hidden message from an image.
    
    Args:
        image: PIL Image or path to image file
        generator: Optional generator for pixel selection (default: sequential)
        shift: Bit shift for LSB position (default: 0)
        encoding: Text encoding (default: "UTF-8")
    
    Returns:
        Decoded message string
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image
    
    if img.mode not in ('RGB', 'RGBA'):
        raise ValueError(f"Unsupported image mode: {img.mode}")
    
    pixels = img.load()
    width, height = img.size
    
    # Determine which pixels to use
    if generator is None:
        pixel_indices = range(width * height)
    else:
        pixel_indices = generator()
    
    # Extract bits
    extracted_bits = []
    
    for pixel_idx in pixel_indices:
        row = pixel_idx // width
        col = pixel_idx % width
        
        if row >= height:
            break
        
        pixel = pixels[col, row]
        
        if isinstance(pixel, int):
            pixel = (pixel, pixel, pixel)
        elif not isinstance(pixel, tuple):
            pixel = tuple(pixel)
        
        # Extract LSB from each channel
        for channel in range(min(len(pixel), 3)):
            bit = (pixel[channel] >> shift) & 1
            extracted_bits.append(bit)
    
    # Extract length (first 32 bits)
    if len(extracted_bits) < 32:
        raise ValueError("Image too small to contain message")
    
    length_bits = extracted_bits[:32]
    length = _bits_to_int(length_bits)
    
    # Extract message bits
    message_bits = extracted_bits[32:32 + length * 8]
    
    if len(message_bits) < length * 8:
        raise ValueError("Incomplete message in image")
    
    # Convert bits to bytes
    message_bytes = _bits_to_bytes(message_bits)
    
    return message_bytes.decode(encoding)


def _bytes_to_bits(data):
    """Convert bytes to list of bits"""
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def _bits_to_bytes(bits):
    """Convert list of bits to bytes"""
    bytes_list = []
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i+8]
        if len(byte_bits) < 8:
            byte_bits.extend([0] * (8 - len(byte_bits)))
        byte = 0
        for bit in byte_bits:
            byte = (byte << 1) | bit
        bytes_list.append(byte)
    return bytes(bytes_list)


def _int_to_bits(value, num_bits):
    """Convert integer to list of bits"""
    bits = []
    for i in range(num_bits - 1, -1, -1):
        bits.append((value >> i) & 1)
    return bits


def _bits_to_int(bits):
    """Convert list of bits to integer"""
    value = 0
    for bit in bits:
        value = (value << 1) | bit
    return value