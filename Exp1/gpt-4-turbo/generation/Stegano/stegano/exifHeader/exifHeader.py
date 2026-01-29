from PIL import Image
import piexif
import os

def hide(input_image_file, output_path, secret_message, **kwargs):
    if isinstance(secret_message, str):
        secret_message = secret_message.encode("UTF-8")
    # Use UserComment tag in Exif
    image = Image.open(input_image_file)
    if "exif" in image.info:
        exif_dict = piexif.load(image.info["exif"])
    else:
        exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
    # UserComment tag is 37510 in Exif
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = b"ASCII\0\0\0" + secret_message
    exif_bytes = piexif.dump(exif_dict)
    image.save(output_path, exif=exif_bytes)
    image.close()

def reveal(image):
    if isinstance(image, str):
        image = Image.open(image)
    if "exif" not in image.info:
        return b""
    exif_dict = piexif.load(image.info["exif"])
    user_comment = exif_dict["Exif"].get(piexif.ExifIFD.UserComment, b"")
    if user_comment.startswith(b"ASCII\0\0\0"):
        return user_comment[8:]
    return user_comment