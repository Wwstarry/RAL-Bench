import piexif
from PIL import Image

def hide(input_image_file, output_path, secret_message=b"", **kwargs):
    """
    Hide a message in the EXIF header (UserComment tag).
    """
    if isinstance(secret_message, str):
        secret_message = secret_message.encode('utf-8')
        
    img = Image.open(input_image_file)
    
    # Load existing exif or create new
    if "exif" in img.info:
        exif_dict = piexif.load(img.info["exif"])
    else:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    # Embed in Exif.UserComment (Tag 37510)
    # piexif expects bytes for UserComment
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = secret_message
    
    exif_bytes = piexif.dump(exif_dict)
    img.save(output_path, exif=exif_bytes)

def reveal(image):
    """
    Reveal a message from the EXIF header.
    """
    if isinstance(image, str):
        img = Image.open(image)
    else:
        img = image
        
    if "exif" not in img.info:
        raise ValueError("No EXIF data found in image")
        
    exif_dict = piexif.load(img.info["exif"])
    
    # Retrieve Exif.UserComment
    if piexif.ExifIFD.UserComment in exif_dict["Exif"]:
        return exif_dict["Exif"][piexif.ExifIFD.UserComment]
    
    return b""