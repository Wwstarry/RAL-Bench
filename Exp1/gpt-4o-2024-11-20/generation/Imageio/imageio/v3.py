# imageio/v3.py

import numpy as np
from pathlib import Path
from PIL import Image, ImageSequence

def imwrite(uri, image):
    """
    Write an image or an animated image to the specified URI.
    
    Parameters:
        uri (str or pathlib.Path): The file path to write the image to.
        image (numpy.ndarray): The image data to write. Can be 2D, 3D, or 4D.
    """
    uri = Path(uri)
    if image.ndim == 2:  # Grayscale image
        img = Image.fromarray(image)
        img.save(uri, format="PNG")
    elif image.ndim == 3:
        if image.shape[2] == 1:  # Grayscale image with single channel
            img = Image.fromarray(image.squeeze(-1))
            img.save(uri, format="PNG")
        elif image.shape[2] == 3:  # RGB image
            img = Image.fromarray(image)
            img.save(uri, format="PNG")
        else:
            raise ValueError("Unsupported 3D array shape for imwrite.")
    elif image.ndim == 4:  # Animated image
        frames = [Image.fromarray(frame) for frame in image]
        frames[0].save(uri, save_all=True, append_images=frames[1:], format="GIF", loop=0)
    else:
        raise ValueError("Unsupported array shape for imwrite.")

def imread(uri):
    """
    Read an image from the specified URI.
    
    Parameters:
        uri (str or pathlib.Path): The file path to read the image from.
    
    Returns:
        numpy.ndarray: The image data as a NumPy array.
    """
    uri = Path(uri)
    with Image.open(uri) as img:
        return np.array(img)

def imiter(uri):
    """
    Return an iterator over the frames of an animated image.
    
    Parameters:
        uri (str or pathlib.Path): The file path to read the image from.
    
    Returns:
        Iterator[numpy.ndarray]: An iterator yielding frames as NumPy arrays.
    """
    uri = Path(uri)
    with Image.open(uri) as img:
        for frame in ImageSequence.Iterator(img):
            yield np.array(frame)

def improps(uri):
    """
    Return the properties of an image, including shape and dtype.
    
    Parameters:
        uri (str or pathlib.Path): The file path to read the image from.
    
    Returns:
        object: An object with `shape` and `dtype` attributes.
    """
    class ImageProps:
        def __init__(self, shape, dtype):
            self.shape = shape
            self.dtype = dtype

    uri = Path(uri)
    with Image.open(uri) as img:
        array = np.array(img)
        return ImageProps(shape=array.shape, dtype=array.dtype)

def immeta(uri):
    """
    Return metadata about the image.
    
    Parameters:
        uri (str or pathlib.Path): The file path to read the image from.
    
    Returns:
        dict: A dictionary containing metadata about the image.
    """
    uri = Path(uri)
    with Image.open(uri) as img:
        return {"mode": img.mode}