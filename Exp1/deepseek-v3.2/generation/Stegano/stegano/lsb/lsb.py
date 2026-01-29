"""
LSB implementation for hiding and revealing messages in images
"""
import itertools
from PIL import Image
from typing import Iterator, Optional, Union
from ..tools.bititerator import BitIterator
from . import generators


def hide(
    image: Union[str, Image.Image],
    message: str,
    generator: Optional[Iterator[int]] = None,
    shift: int = 0,
    encoding: str = "UTF-8",
    auto_convert_rgb: bool = False
) -> Image.Image:
    """
    Hide a message in an image using LSB steganography
    
    Args:
        image: Input image path or PIL Image object
        message: Message to hide
        generator: Iterator yielding pixel indices (default: sequential)
        shift: Number of bits to shift (0-7)
        encoding: Text encoding
        auto_convert_rgb: Convert image to RGB if needed
    
    Returns:
        PIL Image with hidden message
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image.copy()
    
    if auto_convert_rgb and img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGB')
    
    if img.mode in ('P', '1'):
        raise ValueError("Cannot hide in palette or 1-bit images")
    
    # Convert message to bytes
    message_bytes = message.encode(encoding)
    
    # Prepare bit iterator for the message with termination
    bits = BitIterator(message_bytes)
    
    # Get pixel data
    if img.mode in ('RGB', 'RGBA'):
        pixels = img.load()
        width, height = img.size
        
        # Flatten pixel indices
        pixel_count = width * height
        if img.mode == 'RGB':
            channels = 3
        else:  # RGBA
            channels = 4
        
        total_positions = pixel_count * channels
        
        # Use generator or default sequential iterator
        if generator is None:
            gen = range(shift, total_positions, 1)
        else:
            gen = (idx for idx in generator if idx < total_positions)
        
        # Hide bits in LSBs
        for idx in gen:
            if not bits.has_next():
                break
            
            pixel_idx = idx // channels
            channel_idx = idx % channels
            
            x = pixel_idx % width
            y = pixel_idx // width
            
            pixel = list(pixels[x, y])
            current_byte = pixel[channel_idx]
            
            # Clear the LSB and set it to our bit
            bit = bits.next()
            pixel[channel_idx] = (current_byte & ~1) | bit
            
            pixels[x, y] = tuple(pixel)
        
        # Ensure all bits were hidden
        if bits.has_next():
            raise ValueError("Image too small to hide message")
            
    elif img.mode == 'L':  # Grayscale
        pixels = img.load()
        width, height = img.size
        total_positions = width * height
        
        if generator is None:
            gen = range(shift, total_positions, 1)
        else:
            gen = (idx for idx in generator if idx < total_positions)
        
        for idx in gen:
            if not bits.has_next():
                break
            
            x = idx % width
            y = idx // width
            
            current_byte = pixels[x, y]
            bit = bits.next()
            pixels[x, y] = (current_byte & ~1) | bit
        
        if bits.has_next():
            raise ValueError("Image too small to hide message")
    
    else:
        raise ValueError(f"Unsupported image mode: {img.mode}")
    
    return img


def reveal(
    image: Union[str, Image.Image],
    generator: Optional[Iterator[int]] = None,
    shift: int = 0,
    encoding: str = "UTF-8"
) -> str:
    """
    Reveal a hidden message from an image using LSB steganography
    
    Args:
        image: Input image path or PIL Image object
        generator: Iterator yielding pixel indices (default: sequential)
        shift: Number of bits to shift (0-7)
        encoding: Text encoding
    
    Returns:
        Revealed message string
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image
    
    # Get pixel data
    if img.mode in ('RGB', 'RGBA'):
        pixels = img.load()
        width, height = img.size
        pixel_count = width * height
        
        if img.mode == 'RGB':
            channels = 3
        else:  # RGBA
            channels = 4
        
        total_positions = pixel_count * channels
        
        if generator is None:
            gen = range(shift, total_positions, 1)
        else:
            gen = (idx for idx in generator if idx < total_positions)
        
        # Collect bits
        collected_bits = []
        byte_buffer = 0
        bit_count = 0
        
        for idx in gen:
            pixel_idx = idx // channels
            channel_idx = idx % channels
            
            x = pixel_idx % width
            y = pixel_idx // width
            
            pixel = pixels[x, y]
            current_byte = pixel[channel_idx]
            
            # Extract LSB
            bit = current_byte & 1
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
                        break
    
    elif img.mode == 'L':  # Grayscale
        pixels = img.load()
        width, height = img.size
        total_positions = width * height
        
        if generator is None:
            gen = range(shift, total_positions, 1)
        else:
            gen = (idx for idx in generator if idx < total_positions)
        
        collected_bits = []
        byte_buffer = 0
        bit_count = 0
        
        for idx in gen:
            x = idx % width
            y = idx // width
            
            current_byte = pixels[x, y]
            bit = current_byte & 1
            byte_buffer = (byte_buffer << 1) | bit
            bit_count += 1
            
            if bit_count == 8:
                collected_bits.append(byte_buffer)
                byte_buffer = 0
                bit_count = 0
                
                if len(collected_bits) >= 8:
                    if all(b == 0 for b in collected_bits[-8:]):
                        collected_bits = collected_bits[:-8]
                        break
    
    else:
        raise ValueError(f"Unsupported image mode: {img.mode}")
    
    # Convert bytes to string
    message_bytes = bytes(collected_bits)
    return message_bytes.decode(encoding)