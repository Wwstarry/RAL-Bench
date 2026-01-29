from PIL import Image
from stegano.tools.utils import get_mask_and_val, str_to_bin, bin_to_str

def hide(image, message):
    """
    Hide a message in the Red channel of an image.
    """
    if isinstance(image, str):
        image = Image.open(image)
    
    # Ensure RGB
    if image.mode != 'RGB':
        image = image.convert('RGB')
        
    image = image.copy()
    width, height = image.size
    data = image.load()
    
    message_str = str(message) + "\x00"
    binary_message = str_to_bin(message_str)
    
    try:
        for y in range(height):
            for x in range(width):
                try:
                    bit = next(binary_message)
                except StopIteration:
                    return image
                
                r, g, b = data[x, y]
                r = get_mask_and_val(r, bit)
                data[x, y] = (r, g, b)
    except StopIteration:
        pass
        
    return image

def reveal(image):
    """
    Reveal a message hidden in the Red channel.
    """
    if isinstance(image, str):
        image = Image.open(image)
        
    width, height = image.size
    data = image.load()
    
    extracted_bits = []
    
    for y in range(height):
        for x in range(width):
            pixel = data[x, y]
            # Handle if image is not strictly RGB (e.g. RGBA)
            if isinstance(pixel, int):
                # Should not happen if we enforce usage on RGB, but for safety
                r = pixel
            else:
                r = pixel[0]
            
            extracted_bits.append(r & 1)
            
            if len(extracted_bits) % 8 == 0:
                last_byte_bits = extracted_bits[-8:]
                byte_val = 0
                for b in last_byte_bits:
                    byte_val = (byte_val << 1) | b
                
                if byte_val == 0:
                    return bin_to_str(extracted_bits[:-8])
    
    # If no terminator found, try to return what we have (though likely garbage)
    return bin_to_str(extracted_bits)