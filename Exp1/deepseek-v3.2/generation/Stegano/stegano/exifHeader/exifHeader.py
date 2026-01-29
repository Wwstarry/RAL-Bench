"""
EXIF header implementation for hiding and revealing messages
"""
import os
from PIL import Image, ImageFile
from PIL.ExifTags import TAGS
from typing import Union


def hide(
    input_image_file: str,
    output_path: str,
    secret_message: bytes,
    **kwargs
) -> None:
    """
    Hide a message in EXIF header of an image
    
    Args:
        input_image_file: Path to input image
        output_path: Path to save output image
        secret_message: Bytes message to hide
        **kwargs: Additional arguments (unused, for compatibility)
    """
    # Open image
    img = Image.open(input_image_file)
    
    # Get existing EXIF data
    exif_data = img.info.get('exif', b'')
    
    if exif_data:
        # Parse existing EXIF
        from PIL import ExifTags
        exif_dict = img._getexif() or {}
    else:
        exif_dict = {}
    
    # Convert message to hex string for storage
    message_hex = secret_message.hex()
    
    # Store in a custom EXIF tag (using a private tag number)
    # Using tag 0x927C (MakerNote) which is often used for custom data
    exif_dict[0x927C] = message_hex.encode('ascii')
    
    # Save with new EXIF data
    img.save(output_path, exif=exif_dict)


def reveal(image: Union[str, Image.Image]) -> bytes:
    """
    Reveal a hidden message from EXIF header of an image
    
    Args:
        image: Input image path or PIL Image object
    
    Returns:
        Revealed message bytes
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image
    
    # Get EXIF data
    exif_dict = img._getexif()
    
    if not exif_dict:
        return b''
    
    # Look for our custom tag
    message_data = exif_dict.get(0x927C)
    
    if not message_data:
        return b''
    
    # Convert from hex string back to bytes
    try:
        if isinstance(message_data, bytes):
            message_str = message_data.decode('ascii')
        else:
            message_str = str(message_data)
        
        return bytes.fromhex(message_str)
    except (ValueError, UnicodeDecodeError):
        return b''