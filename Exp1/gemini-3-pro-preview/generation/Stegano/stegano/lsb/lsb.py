import sys
from PIL import Image
from stegano.tools.utils import get_mask_and_val, str_to_bin, bin_to_str
from stegano.lsb import generators

def hide(image, message, generator=None, shift=0, encoding="UTF-8", auto_convert_rgb=False):
    """
    Hide a message (string) in an image using LSB steganography.
    """
    if isinstance(image, str):
        image = Image.open(image)
    
    if auto_convert_rgb and image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Copy image to avoid modifying the original object in memory if it's passed by reference
    image = image.copy()
    
    # Append a null terminator to the message to mark the end
    # This allows reveal to know when to stop
    message_str = str(message) + "\x00"
    
    # Convert message to a generator of bits
    binary_message = str_to_bin(message_str, encoding=encoding)
    
    width, height = image.size
    data = image.load()
    
    # Create the coordinate generator
    if generator is None:
        # Default: Linear iteration
        def linear_generator():
            for y in range(height):
                for x in range(width):
                    yield (x, y)
        coords = linear_generator()
    else:
        # Use provided generator (which yields integers) to map to coordinates
        # We assume the generator yields a flat index
        def mapped_generator():
            gen = generator()
            for i in gen:
                # Convert flat index to (x, y)
                # Note: This assumes the generator yields indices within bounds
                # If the generator yields large numbers, we wrap or check bounds
                if i >= width * height:
                    continue
                yield (i % width, i // width)
        coords = mapped_generator()

    # Skip 'shift' pixels
    for _ in range(shift):
        next(coords, None)

    try:
        for x, y in coords:
            # Get next bit to hide
            try:
                bit = next(binary_message)
            except StopIteration:
                break
            
            # Get current pixel
            pixel = data[x, y]
            
            # Handle different modes (RGB vs RGBA vs others)
            # We modify the LSB of the first channel (Red or Gray) usually, 
            # or distribute across channels. The reference Stegano usually 
            # iterates through channels of a pixel if needed, but basic LSB 
            # often just picks one channel or iterates channels linearly.
            # To be robust and match typical behavior:
            # We will modify the channels sequentially for each pixel if we treat
            # the image as a flat stream of bytes, but here we are pixel-based.
            # Let's modify the Red channel (index 0) for simplicity, or iterate channels.
            # Reference Stegano LSB typically iterates over the flattened bands of the image.
            # However, with the generator yielding (x,y), we are at pixel level.
            # Let's modify the Red channel (0), then Green (1), then Blue (2).
            
            # Actually, to support the generator properly, we should consume one coordinate
            # per bit or per 3 bits? 
            # The reference implementation for LSB with generators usually hides 
            # 3 bits per pixel (RGB) or 1 bit per pixel?
            # Let's stick to 1 bit per pixel (Red channel) to ensure the generator logic 
            # (which yields one index) aligns with one modification.
            
            # Modify the first channel (usually Red)
            if isinstance(pixel, int):
                # Grayscale
                pixel = get_mask_and_val(pixel, bit)
                data[x, y] = pixel
            else:
                # Tuple (R, G, B) or (R, G, B, A)
                p_list = list(pixel)
                p_list[0] = get_mask_and_val(p_list[0], bit)
                data[x, y] = tuple(p_list)
                
    except StopIteration:
        # Image full or generator exhausted
        pass

    return image

def reveal(image, generator=None, shift=0, encoding="UTF-8"):
    """
    Reveal a message hidden in an image using LSB steganography.
    """
    if isinstance(image, str):
        image = Image.open(image)
        
    width, height = image.size
    data = image.load()
    
    # Create the coordinate generator
    if generator is None:
        def linear_generator():
            for y in range(height):
                for x in range(width):
                    yield (x, y)
        coords = linear_generator()
    else:
        def mapped_generator():
            gen = generator()
            for i in gen:
                if i >= width * height:
                    continue
                yield (i % width, i // width)
        coords = mapped_generator()

    # Skip 'shift' pixels
    for _ in range(shift):
        next(coords, None)

    extracted_bits = []
    
    for x, y in coords:
        pixel = data[x, y]
        
        # Extract LSB from first channel
        if isinstance(pixel, int):
            val = pixel
        else:
            val = pixel[0]
            
        extracted_bits.append(val & 1)
        
        # Optimization: Check for null terminator every 8 bits
        if len(extracted_bits) % 8 == 0:
            # Check the last 8 bits
            last_byte_bits = extracted_bits[-8:]
            byte_val = 0
            for b in last_byte_bits:
                byte_val = (byte_val << 1) | b
            
            if byte_val == 0:
                # Null terminator found
                # Remove the null byte bits
                extracted_bits = extracted_bits[:-8]
                break
    
    return bin_to_str(extracted_bits, encoding=encoding)