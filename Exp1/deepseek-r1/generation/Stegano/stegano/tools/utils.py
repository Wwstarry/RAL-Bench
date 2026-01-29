from PIL import Image

def convert_image(image):
    if image.mode not in ('RGB', 'RGBA'):
        return image.convert('RGB')
    return image

def get_image_pixel_count(image):
    return image.width * image.height