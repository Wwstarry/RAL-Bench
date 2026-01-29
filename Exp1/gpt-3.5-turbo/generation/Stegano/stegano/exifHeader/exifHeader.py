from PIL import Image
import piexif
import os


def hide(input_image_file: str, output_path: str, secret_message: bytes, **kwargs) -> None:
    """
    Hide a byte message in the EXIF UserComment tag of a JPEG or TIFF image.

    :param input_image_file: path to input image file (JPEG or TIFF)
    :param output_path: path to write output image file with hidden message
    :param secret_message: bytes message to hide
    :param kwargs: ignored for compatibility
    """
    # Load image and exif data
    img = Image.open(input_image_file)
    if img.format not in ("JPEG", "TIFF"):
        raise ValueError("Unsupported image format for exifHeader: {}".format(img.format))

    exif_dict = {}
    if "exif" in img.info:
        exif_dict = piexif.load(img.info["exif"])
    else:
        # Create empty exif dict structure
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}

    # UserComment tag is in Exif IFD, tag 37510
    # According to EXIF spec, UserComment starts with 8 bytes charset code
    # We'll use ASCII code prefix b'ASCII\x00\x00\x00' + message
    prefix = b'ASCII\x00\x00\x00'
    user_comment = prefix + secret_message

    exif_dict["Exif"][piexif.ExifIFD.UserComment] = user_comment

    exif_bytes = piexif.dump(exif_dict)

    # Save image with new exif
    img.save(output_path, exif=exif_bytes)


def reveal(image: Image.Image) -> bytes:
    """
    Reveal a hidden byte message from the EXIF UserComment tag of a PIL Image.

    :param image: PIL Image object
    :return: extracted byte message
    """
    if "exif" not in image.info:
        return b""

    exif_dict = piexif.load(image.info["exif"])
    user_comment = exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment, b"")

    if not user_comment:
        return b""

    # Remove charset prefix if present
    if user_comment.startswith(b'ASCII\x00\x00\x00'):
        return user_comment[8:]
    else:
        return user_comment