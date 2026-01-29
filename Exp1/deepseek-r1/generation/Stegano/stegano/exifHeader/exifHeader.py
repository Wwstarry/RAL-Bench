import piexif
from PIL import Image

def hide(input_image_file, output_path, secret_message):
    exif_dict = piexif.load(input_image_file)
    if isinstance(secret_message, str):
        secret_message = secret_message.encode()
    exif_dict["Exif"][piexif.ExifIFD.UserComment] = secret_message
    exif_bytes = piexif.dump(exif_dict)
    
    img = Image.open(input_image_file)
    img.save(output_path, exif=exif_bytes)

def reveal(image):
    exif_dict = piexif.load(image)
    return exif_dict.get("Exif", {}).get(piexif.ExifIFD.UserComment, b"")