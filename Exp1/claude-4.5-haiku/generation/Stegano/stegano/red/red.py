"""
Red channel steganography implementation
"""

from PIL import Image


def hide(image, message):
    """
    Hide a message in the red channel of an image.
    
    Args:
        image: PIL Image or path to image file
        message: String message to hide
    
    Returns:
        PIL Image with hidden message in red channel
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image.copy()
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Encode message
    message_bytes = message.encode('UTF-8')
    message_bits = _bytes_to_bits(message_bytes)
    
    # Add length header (32 bits)
    length = len(message_bytes)
    length_bits = _int_to_bits(length, 32)
    all_bits = length_bits + message_bits
    
    # Get pixel data
    pixels = img.load()
    width, height = img.size
    
    bit_index = 0
    
    for y in range(height):
        for x in range(width):
            if bit_index >= len(all_bits):
                break
            
            r, g, b = pixels[x, y]
            
            # Modify red channel LSB
            bit = all_bits[bit_index]
            bit_index += 1
            
            r = (r & 0xFE) | bit
            pixels[x, y] = (r, g, b)
        
        if bit_index >= len(all_bits):
            break
    
    return img


def reveal(image):
    """
    Reveal a hidden message from the red channel of an image.
    
    Args:
        image: PIL Image or path to image file
    
    Returns:
        Decoded message string
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    pixels = img.load()
    width, height = img.size
    
    # Extract bits from red channel
    extracted_bits = []
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            bit = r & 1
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
    
    return message_bytes.decode('UTF-8')


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