"""
EXIF header steganography implementation
"""

from PIL import Image
import piexif
import io


def hide(input_image_file, output_image_file, secret_message, 
         exif_tag="UserComment", auto_convert_rgb=False):
    """
    Hide a message in EXIF metadata.
    
    Args:
        input_image_file: Path to input image
        output_image_file: Path to output image
        secret_message: Bytes or string message to hide
        exif_tag: EXIF tag to use (default: UserComment)
        auto_convert_rgb: Convert to RGB if needed
        
    Returns:
        Path to output file
    """
    img = Image.open(input_image_file)
    
    # Convert message to bytes if string
    if isinstance(secret_message, str):
        secret_message = secret_message.encode('UTF-8')
    
    # Load existing EXIF data or create new
    try:
        exif_dict = piexif.load(input_image_file)
    except:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
    
    # Store message in UserComment field
    if exif_tag == "UserComment":
        # UserComment format: encoding prefix + data
        exif_dict["Exif"][piexif.ExifIFD.UserComment] = secret_message
    
    # Convert EXIF dict to bytes
    try:
        exif_bytes = piexif.dump(exif_dict)
    except:
        # If dump fails, create minimal EXIF
        exif_dict = {"0th": {}, "Exif": {piexif.ExifIFD.UserComment: secret_message}, 
                     "GPS": {}, "1st": {}, "thumbnail": None}
        exif_bytes = piexif.dump(exif_dict)
    
    # Save image with EXIF data
    if img.mode not in ('RGB', 'L'):
        if auto_convert_rgb:
            img = img.convert('RGB')
    
    img.save(output_image_file, exif=exif_bytes)
    
    return output_image_file


def reveal(input_image_file):
    """
    Reveal a hidden message from EXIF metadata.
    
    Args:
        input_image_file: Path to image file or PIL Image object
        
    Returns:
        Bytes message
    """
    if isinstance(input_image_file, str):
        try:
            exif_dict = piexif.load(input_image_file)
        except:
            return b""
    else:
        # PIL Image object
        try:
            exif_data = input_image_file.info.get('exif', b'')
            if exif_data:
                exif_dict = piexif.load(exif_data)
            else:
                return b""
        except:
            return b""
    
    # Try to get UserComment
    if "Exif" in exif_dict and piexif.ExifIFD.UserComment in exif_dict["Exif"]:
        message = exif_dict["Exif"][piexif.ExifIFD.UserComment]
        if isinstance(message, bytes):
            return message
    
    return b""