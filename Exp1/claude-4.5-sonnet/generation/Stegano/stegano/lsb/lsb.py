"""
LSB steganography implementation
"""

from PIL import Image
from stegano.lsb import generators as gens


def hide(input_image, message, generator=None, shift=0, encoding="UTF-8", auto_convert_rgb=False):
    """
    Hide a message in an image using LSB steganography.
    
    Args:
        input_image: Path to image file or PIL Image object
        message: String message to hide
        generator: Optional generator for pixel selection (default: sequential)
        shift: Offset for generator sequence
        encoding: Text encoding (default: UTF-8)
        auto_convert_rgb: Convert image to RGB if needed
        
    Returns:
        PIL Image object with hidden message
    """
    if isinstance(input_image, str):
        img = Image.open(input_image)
    else:
        img = input_image.copy()
    
    # Convert to RGB if needed
    if img.mode not in ('RGB', 'RGBA'):
        if auto_convert_rgb:
            img = img.convert('RGB')
        else:
            raise ValueError(f"Image mode {img.mode} not supported. Use auto_convert_rgb=True or convert to RGB.")
    
    # Encode message to bytes and add null terminator
    message_bytes = message.encode(encoding)
    message_bytes += b'\x00\x00\x00\x00'  # 4-byte null terminator
    
    # Convert bytes to bits
    bits = []
    for byte in message_bytes:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    
    # Get image dimensions
    width, height = img.size
    pixels = img.load()
    
    # Create generator for pixel positions
    if generator is None:
        # Sequential generator
        def sequential_gen():
            idx = 0
            while True:
                yield idx
                idx += 1
        gen = sequential_gen()
    else:
        gen = generator()
    
    # Skip 'shift' positions
    for _ in range(shift):
        next(gen)
    
    # Hide bits in image
    bit_index = 0
    total_bits = len(bits)
    
    while bit_index < total_bits:
        pos = next(gen)
        x = pos % width
        y = pos // width
        
        if y >= height:
            raise ValueError("Message too long for image")
        
        pixel = list(pixels[x, y])
        
        # Hide bits in RGB channels (skip alpha if RGBA)
        channels = 3 if img.mode == 'RGB' else 3  # Only use RGB channels
        for channel in range(channels):
            if bit_index >= total_bits:
                break
            
            # Clear LSB and set new bit
            pixel[channel] = (pixel[channel] & 0xFE) | bits[bit_index]
            bit_index += 1
        
        pixels[x, y] = tuple(pixel)
        
        if bit_index >= total_bits:
            break
    
    return img


def reveal(input_image, generator=None, shift=0, encoding="UTF-8"):
    """
    Reveal a hidden message from an image.
    
    Args:
        input_image: Path to image file or PIL Image object
        generator: Optional generator for pixel selection (default: sequential)
        shift: Offset for generator sequence
        encoding: Text encoding (default: UTF-8)
        
    Returns:
        Decoded message string
    """
    if isinstance(input_image, str):
        img = Image.open(input_image)
    else:
        img = input_image
    
    width, height = img.size
    pixels = img.load()
    
    # Create generator for pixel positions
    if generator is None:
        # Sequential generator
        def sequential_gen():
            idx = 0
            while True:
                yield idx
                idx += 1
        gen = sequential_gen()
    else:
        gen = generator()
    
    # Skip 'shift' positions
    for _ in range(shift):
        next(gen)
    
    # Extract bits
    bits = []
    null_count = 0
    max_bytes = width * height * 3 // 8  # Maximum possible bytes
    
    for _ in range(max_bytes * 8):
        pos = next(gen)
        x = pos % width
        y = pos // width
        
        if y >= height:
            break
        
        pixel = pixels[x, y]
        
        # Extract bits from RGB channels
        channels = 3 if img.mode == 'RGB' else 3
        for channel in range(channels):
            if isinstance(pixel, int):
                # Grayscale
                bit = pixel & 1
            else:
                bit = pixel[channel] & 1
            bits.append(bit)
            
            # Check for null terminator every 8 bits
            if len(bits) % 8 == 0:
                byte_val = 0
                for i in range(8):
                    byte_val = (byte_val << 1) | bits[-(8-i)]
                
                if byte_val == 0:
                    null_count += 1
                    if null_count == 4:  # Found 4-byte null terminator
                        # Remove null terminator bits
                        bits = bits[:-32]
                        # Convert bits to bytes
                        message_bytes = bytearray()
                        for i in range(0, len(bits), 8):
                            if i + 8 <= len(bits):
                                byte_val = 0
                                for j in range(8):
                                    byte_val = (byte_val << 1) | bits[i + j]
                                message_bytes.append(byte_val)
                        
                        return message_bytes.decode(encoding, errors='ignore')
                else:
                    null_count = 0
    
    # If no terminator found, return empty string
    return ""