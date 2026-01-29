"""
Red channel steganography implementation
"""

from PIL import Image


def hide(input_image, message):
    """
    Hide a message in the red channel of an image.
    
    Args:
        input_image: Path to image file or PIL Image object
        message: String message to hide
        
    Returns:
        PIL Image object with hidden message
    """
    if isinstance(input_image, str):
        img = Image.open(input_image)
    else:
        img = input_image.copy()
    
    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Encode message and add terminator
    message_bytes = message.encode('UTF-8')
    message_bytes += b'\x00'  # Null terminator
    
    width, height = img.size
    pixels = img.load()
    
    byte_index = 0
    bit_index = 0
    
    for y in range(height):
        for x in range(width):
            if byte_index >= len(message_bytes):
                return img
            
            r, g, b = pixels[x, y]
            
            # Get current bit from message
            current_byte = message_bytes[byte_index]
            bit = (current_byte >> (7 - bit_index)) & 1
            
            # Modify red channel LSB
            r = (r & 0xFE) | bit
            
            pixels[x, y] = (r, g, b)
            
            bit_index += 1
            if bit_index == 8:
                bit_index = 0
                byte_index += 1
    
    return img


def reveal(input_image):
    """
    Reveal a hidden message from the red channel of an image.
    
    Args:
        input_image: Path to image file or PIL Image object
        
    Returns:
        Decoded message string
    """
    if isinstance(input_image, str):
        img = Image.open(input_image)
    else:
        img = input_image
    
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    width, height = img.size
    pixels = img.load()
    
    bits = []
    message_bytes = bytearray()
    
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            # Extract LSB from red channel
            bit = r & 1
            bits.append(bit)
            
            # Every 8 bits, form a byte
            if len(bits) == 8:
                byte_val = 0
                for i in range(8):
                    byte_val = (byte_val << 1) | bits[i]
                
                if byte_val == 0:
                    # Found null terminator
                    return message_bytes.decode('UTF-8', errors='ignore')
                
                message_bytes.append(byte_val)
                bits = []
    
    return message_bytes.decode('UTF-8', errors='ignore')