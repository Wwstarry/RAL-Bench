from PIL import Image
from PIL.ExifTags import TAGS
import piexif

def hide(input_image_file, output_path, secret_message):
    exif_dict = piexif.load(input_image_file)
    exif_dict["0th"][piexif.ImageIFD.Make] = secret_message.decode("utf-8")
    exif_bytes = piexif.dump(exif_dict)
    image = Image.open(input_image_file)
    image.save(output_path, exif=exif_bytes)

def reveal(image):
    exif_dict = piexif.load(image)
    return exif_dict["0th"].get(piexif.ImageIFD.Make, "").encode("utf-8")