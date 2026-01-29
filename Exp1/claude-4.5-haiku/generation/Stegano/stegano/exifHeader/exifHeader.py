"""
EXIF header steganography implementation
"""

from PIL import Image
from PIL.Image import Exif
import io


def hide(input_image_file, output_path, secret_message=b'', **kwargs):
    """
    Hide a message in EXIF header of an image.
    
    Args:
        input_image_file: Path to input image or PIL Image
        output_path: Path where output image will be written
        secret_message: Bytes message to hide (default: empty)
        **kwargs: Additional arguments
    
    Returns:
        None (writes to output_path)
    """
    if isinstance(input_image_file, str):
        img = Image.open(input_image_file)
    else:
        img = input_image_file.copy()
    
    if isinstance(secret_message, str):
        secret_message = secret_message.encode('UTF-8')
    
    # Create EXIF data
    try:
        exif = img.getexif()
    except:
        exif = Exif()
    
    # Store message in UserComment tag (37510)
    # Encode as UTF-8 with length prefix
    message_with_length = len(secret_message).to_bytes(4, 'big') + secret_message
    
    # Store in a custom tag or use UserComment
    exif[37510] = message_with_length
    
    # Save image with EXIF data
    img.save(output_path, exif=exif)


def reveal(image):
    """
    Reveal a hidden message from EXIF header.
    
    Args:
        image: PIL Image or path to image file
    
    Returns:
        Bytes message extracted from EXIF
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image
    
    try:
        exif = img.getexif()
    except:
        return b''
    
    # Try to extract from UserComment tag (37510)
    if 37510 in exif:
        data = exif[37510]
        if isinstance(data, bytes) and len(data) >= 4:
            length = int.from_bytes(data[:4], 'big')
            return data[4:4+length]
        return data
    
    return b''