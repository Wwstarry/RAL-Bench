# stegano/exifHeader/exifHeader.py
import piexif
from piexif import ExifIFD

def hide(input_image_file, output_path, secret_message):
    """
    Hides a byte message in the EXIF header of a JPEG/TIFF image.
    The message is stored in the UserComment tag (0x9286).
    """
    if not isinstance(secret_message, bytes):
        raise TypeError("The secret_message must be a bytes object.")

    try:
        exif_dict = piexif.load(input_image_file)
    except Exception:
        # If no EXIF data, create a new dictionary
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    # The UserComment tag is used to store the secret message.
    # piexif handles the encoding prefix (e.g., 'ASCII\x00\x00\x00') for us.
    exif_dict["Exif"][ExifIFD.UserComment] = secret_message

    try:
        exif_bytes = piexif.dump(exif_dict)
        # piexif.insert copies the image data from input and inserts the new exif.
        piexif.insert(exif_bytes, input_image_file, output_path)
    except Exception as e:
        raise IOError(f"Failed to write EXIF data to {output_path}") from e


def reveal(image):
    """
    Reveals a byte message hidden in the EXIF UserComment tag of an image.
    'image' should be a file path.
    """
    try:
        exif_dict = piexif.load(image)
        user_comment = exif_dict.get("Exif", {}).get(ExifIFD.UserComment)
        
        if user_comment is None:
            raise ValueError("No hidden message found in EXIF UserComment tag.")
            
        # piexif returns the UserComment value directly as bytes,
        # stripping the character code prefix.
        return user_comment
        
    except FileNotFoundError:
        raise
    except Exception as e:
        # This can catch piexif._exceptions.InvalidImageDataError etc.
        raise ValueError("Failed to read EXIF data or find message.") from e