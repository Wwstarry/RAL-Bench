"""
ImageIO v3 API implementation
Provides high-level image I/O functions compatible with ImageIO v3
"""

import io
import pathlib
from typing import Union, Iterator, Dict, Any
import numpy as np

try:
    from PIL import Image, ImageSequence
except ImportError:
    raise ImportError(
        "The imageio library requires Pillow. Please install it with: pip install Pillow"
    )


def imwrite(uri: Union[str, pathlib.Path], image: np.ndarray) -> None:
    """
    Write an image or animated image to disk.
    
    Args:
        uri: File path to write to
        image: NumPy array containing image data
            - 2D (H, W) or 3D (H, W, C) with C=1 or 3: single image
            - 3D (N, H, W) or 4D (N, H, W, C): animated image with N frames
    
    Raises:
        ValueError: If image shape is invalid
        IOError: If writing fails
    """
    uri = str(uri)  # Convert pathlib.Path to string
    
    # Validate input array
    if not isinstance(image, np.ndarray):
        raise TypeError("image must be a NumPy array")
    
    if image.dtype != np.uint8:
        raise ValueError("Only uint8 arrays are supported")
    
    ndim = image.ndim
    if ndim not in (2, 3, 4):
        raise ValueError(f"Expected 2, 3, or 4 dimensions, got {ndim}")
    
    # Determine if this is an animated image
    is_animated = ndim in (3, 4) and (ndim == 3 or (ndim == 4 and image.shape[3] in (1, 3)))
    if is_animated and ndim == 3:
        # (N, H, W) grayscale animation
        n_frames, height, width = image.shape
        mode = "L"
        frames_data = [image[i] for i in range(n_frames)]
    elif is_animated and ndim == 4:
        # (N, H, W, C) color animation
        n_frames, height, width, channels = image.shape
        if channels == 1:
            mode = "L"
            frames_data = [image[i, :, :, 0] for i in range(n_frames)]
        else:  # channels == 3
            mode = "RGB"
            frames_data = [image[i] for i in range(n_frames)]
    elif ndim == 2:
        # Single grayscale image
        height, width = image.shape
        mode = "L"
        frames_data = [image]
    elif ndim == 3:
        # Single color image
        height, width, channels = image.shape
        if channels == 1:
            mode = "L"
            frames_data = [image[:, :, 0]]
        else:  # channels == 3
            mode = "RGB"
            frames_data = [image]
    else:
        raise ValueError(f"Invalid image shape: {image.shape}")
    
    # Convert to PIL images
    pil_images = []
    for frame in frames_data:
        if frame.ndim == 2:
            pil_img = Image.fromarray(frame, mode=mode)
        else:
            pil_img = Image.fromarray(frame, mode=mode)
        pil_images.append(pil_img)
    
    # Save to file
    if len(pil_images) == 1:
        # Single image - save as PNG
        pil_images[0].save(uri, format='PNG')
    else:
        # Animated image - save as GIF
        pil_images[0].save(
            uri,
            format='GIF',
            save_all=True,
            append_images=pil_images[1:],
            duration=100,  # 100ms per frame
            loop=0  # infinite loop
        )


def imread(uri: Union[str, pathlib.Path]) -> np.ndarray:
    """
    Read an image from disk.
    
    Args:
        uri: File path to read from
        
    Returns:
        NumPy array containing the image data
    """
    uri = str(uri)
    
    with Image.open(uri) as img:
        # Convert to RGB if necessary to ensure consistent output
        if img.mode in ('P', 'PA'):
            img = img.convert('RGBA' if 'A' in img.mode else 'RGB')
        elif img.mode == '1':
            img = img.convert('L')
        
        arr = np.array(img)
        
        # Handle single-channel images properly
        if arr.ndim == 3 and arr.shape[2] == 1:
            arr = arr[:, :, 0]
        
        return arr


def imiter(uri: Union[str, pathlib.Path]) -> Iterator[np.ndarray]:
    """
    Iterate over frames of an image.
    
    Args:
        uri: File path to read from
        
    Yields:
        NumPy arrays, one per frame
    """
    uri = str(uri)
    
    with Image.open(uri) as img:
        for frame in ImageSequence.Iterator(img):
            # Convert to RGB if necessary
            if frame.mode in ('P', 'PA'):
                frame = frame.convert('RGBA' if 'A' in frame.mode else 'RGB')
            elif frame.mode == '1':
                frame = frame.convert('L')
            
            arr = np.array(frame)
            
            # Handle single-channel images properly
            if arr.ndim == 3 and arr.shape[2] == 1:
                arr = arr[:, :, 0]
            
            yield arr


def improps(uri: Union[str, pathlib.Path]) -> Any:
    """
    Get properties of an image.
    
    Args:
        uri: File path to read from
        
    Returns:
        Object with shape and dtype attributes
    """
    uri = str(uri)
    
    class ImageProperties:
        def __init__(self, shape: tuple, dtype: np.dtype):
            self.shape = shape
            self.dtype = dtype
    
    with Image.open(uri) as img:
        # Get shape by reading first frame
        first_frame = next(ImageSequence.Iterator(img))
        if first_frame.mode in ('P', 'PA'):
            first_frame = first_frame.convert('RGBA' if 'A' in first_frame.mode else 'RGB')
        elif first_frame.mode == '1':
            first_frame = first_frame.convert('L')
        
        arr = np.array(first_frame)
        if arr.ndim == 3 and arr.shape[2] == 1:
            arr = arr[:, :, 0]
        
        # Count frames
        frame_count = 0
        img_copy = Image.open(uri)  # Need to reopen to reset iterator
        for _ in ImageSequence.Iterator(img_copy):
            frame_count += 1
        img_copy.close()
        
        # Determine final shape
        if frame_count > 1:
            # Animated image
            if arr.ndim == 2:
                shape = (frame_count, arr.shape[0], arr.shape[1])
            else:
                shape = (frame_count, arr.shape[0], arr.shape[1], arr.shape[2])
        else:
            # Single image
            shape = arr.shape
        
        return ImageProperties(shape, arr.dtype)


def immeta(uri: Union[str, pathlib.Path]) -> Dict[str, Any]:
    """
    Get metadata of an image.
    
    Args:
        uri: File path to read from
        
    Returns:
        Dictionary containing image metadata
    """
    uri = str(uri)
    
    with Image.open(uri) as img:
        metadata = {
            "mode": img.mode,
            "size": img.size,
            "format": img.format,
        }
        
        # Add format-specific metadata
        if hasattr(img, 'info'):
            metadata.update(img.info)
        
        return metadata