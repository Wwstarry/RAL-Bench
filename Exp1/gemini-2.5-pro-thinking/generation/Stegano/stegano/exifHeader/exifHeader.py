# This module requires the 'piexif' library.
# You can install it with: pip install piexif
import piexif

USER_COMMENT_TAG = piexif.ExifIFD.UserComment
COMMENT_HEADER = b'ASCII\x00\x00\x00'

def hide(input_image_file: str, output_path: str, secret_message: bytes):
    """
    Hides a byte message in the EXIF header of a JPEG/TIFF image.

    :param input_image_file: Path to the input image.
    :param output_path: Path to save the output image.
    :param secret_message: The message to hide, as bytes.
    """
    if not isinstance(secret_message, bytes):
        raise TypeError("secret_message must be bytes.")

    try:
        exif_dict = piexif.load(input_image_file)
    except piexif.InvalidImageDataError:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
    except Exception:
        raise

    comment_data = COMMENT_HEADER + secret_message
    exif_dict["Exif"][USER_COMMENT_TAG] = comment_data
    
    try:
        exif_bytes = piexif.dump(exif_dict)
    except Exception as e:
        raise ValueError(f"Failed to dump EXIF data: {e}")

    try:
        piexif.insert(exif_bytes, input_image_file, output_path)
    except Exception as e:
        raise IOError(f"Failed to write output file: {e}")

def reveal(image: str) -> bytes:
    """
    Reveals a byte message hidden in the EXIF header.

    :param image: Path to the image file.
    :return: The revealed message as bytes, or None if not found.
    """
    try:
        exif_dict = piexif.load(image)
    except Exception:
        return None

    user_comment = exif_dict.get("Exif", {}).get(USER_COMMENT_TAG)
    
    if user_comment and user_comment.startswith(COMMENT_HEADER):
        return user_comment[len(COMMENT_HEADER):]
    
    return None