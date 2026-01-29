"""
EXIF header steganography implementation.
Hides and reveals messages in the EXIF metadata of JPEG/TIFF images.
"""
import os
import sys
import piexif
from typing import Union, Optional

def hide(
    input_image_file: str,
    output_path: str,
    secret_message: bytes,
    key: Optional[str] = None,
    exif_field: str = "ImageDescription"
) -> None:
    """
    Hide a message in the EXIF headers of a JPEG/TIFF image.
    
    Args:
        input_image_file: Path to the input image
        output_path: Path where the output image will be saved
        secret_message: Binary message to hide
        key: Encryption key (not implemented in this version)
        exif_field: EXIF field where the message will be stored
        
    Returns:
        None
    """
    # Verify the input file exists
    if not os.path.isfile(input_image_file):
        raise FileNotFoundError(f"Input image file not found: {input_image_file}")
    
    # Map of common EXIF fields to their IFD and tag identifier
    exif_field_map = {
        "ImageDescription": ("0th", piexif.ImageIFD.ImageDescription),
        "UserComment": ("Exif", piexif.ExifIFD.UserComment),
        "Copyright": ("0th", piexif.ImageIFD.Copyright),
        "Artist": ("0th", piexif.ImageIFD.Artist),
    }
    
    if exif_field not in exif_field_map:
        raise ValueError(f"Unsupported EXIF field: {exif_field}")
    
    # Get EXIF data from the image
    try:
        exif_dict = piexif.load(input_image_file)
    except:
        # If the image has no EXIF data, create an empty dictionary
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "Interop": {}, "1st": {}}
    
    # Get the IFD and tag for the selected field
    ifd, tag = exif_field_map[exif_field]
    
    # Store the secret message in the selected EXIF field
    if exif_field == "UserComment":
        # UserComment needs a specific format
        exif_dict[ifd][tag] = b"ASCII\x00\x00\x00" + secret_message
    else:
        exif_dict[ifd][tag] = secret_message
    
    # Convert the EXIF dictionary to bytes
    exif_bytes = piexif.dump(exif_dict)
    
    # Insert the EXIF data into the image and save it
    piexif.insert(exif_bytes, input_image_file, output_path)

def reveal(
    image: str,
    key: Optional[str] = None,
    exif_field: str = "ImageDescription"
) -> bytes:
    """
    Reveal a message hidden in the EXIF headers of a JPEG/TIFF image.
    
    Args:
        image: Path to the image
        key: Decryption key (not implemented in this version)
        exif_field: EXIF field where the message is stored
        
    Returns:
        The hidden binary message
    """
    # Verify the input file exists
    if not os.path.isfile(image):
        raise FileNotFoundError(f"Image file not found: {image}")
    
    # Map of common EXIF fields to their IFD and tag identifier
    exif_field_map = {
        "ImageDescription": ("0th", piexif.ImageIFD.ImageDescription),
        "UserComment": ("Exif", piexif.ExifIFD.UserComment),
        "Copyright": ("0th", piexif.ImageIFD.Copyright),
        "Artist": ("0th", piexif.ImageIFD.Artist),
    }
    
    if exif_field not in exif_field_map:
        raise ValueError(f"Unsupported EXIF field: {exif_field}")
    
    # Get EXIF data from the image
    try:
        exif_dict = piexif.load(image)
    except:
        raise ValueError("No EXIF data found in the image")
    
    # Get the IFD and tag for the selected field
    ifd, tag = exif_field_map[exif_field]
    
    # Extract the secret message from the selected EXIF field
    if tag not in exif_dict[ifd]:
        raise ValueError(f"No data found in the {exif_field} field")
    
    secret_data = exif_dict[ifd][tag]
    
    # For UserComment, remove the ASCII header
    if exif_field == "UserComment" and secret_data.startswith(b"ASCII\x00\x00\x00"):
        secret_data = secret_data[8:]
    
    return secret_data