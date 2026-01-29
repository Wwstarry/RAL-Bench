# imageio/v3.py

import numpy as np
from pathlib import Path
from typing import Any, Iterator, Dict

try:
    from PIL import Image, ImageSequence
except ImportError:
    raise ImportError("imageio.v3 requires Pillow (PIL) to be installed.")

# --- Helper functions ---

def _normalize_path(uri):
    if isinstance(uri, Path):
        return str(uri)
    elif isinstance(uri, str):
        return uri
    else:
        raise TypeError(f"uri must be a string or pathlib.Path, got {type(uri)}")

def _is_animated_shape(shape):
    # (N, H, W) or (N, H, W, C)
    if len(shape) == 3:
        return True  # (N, H, W)
    if len(shape) == 4:
        return True  # (N, H, W, C)
    return False

def _is_single_image_shape(shape):
    # (H, W) or (H, W, C)
    if len(shape) == 2:
        return True
    if len(shape) == 3 and (shape[2] == 1 or shape[2] == 3):
        return True
    return False

def _ensure_uint8(arr):
    if arr.dtype == np.uint8:
        return arr
    # Convert to uint8 (clip if necessary)
    return np.clip(arr, 0, 255).astype(np.uint8)

def _to_pil_image(arr):
    arr = _ensure_uint8(arr)
    if arr.ndim == 2:
        return Image.fromarray(arr, mode="L")
    elif arr.ndim == 3:
        if arr.shape[2] == 1:
            return Image.fromarray(arr[..., 0], mode="L")
        elif arr.shape[2] == 3:
            return Image.fromarray(arr, mode="RGB")
        else:
            raise ValueError(f"Unsupported channel count: {arr.shape[2]}")
    else:
        raise ValueError(f"Unsupported array shape for image: {arr.shape}")

def _from_pil_image(img, dtype):
    arr = np.array(img)
    if dtype is not None and arr.dtype != dtype:
        arr = arr.astype(dtype)
    return arr

def _guess_format_from_path(path):
    ext = Path(path).suffix.lower()
    if ext in [".png"]:
        return "PNG"
    elif ext in [".gif"]:
        return "GIF"
    else:
        # Default to PNG
        return "PNG"

def _get_mode_from_shape(shape):
    if len(shape) == 2:
        return "L"
    elif len(shape) == 3:
        if shape[2] == 1:
            return "L"
        elif shape[2] == 3:
            return "RGB"
    raise ValueError(f"Cannot determine mode from shape {shape}")

# --- API functions ---

def imwrite(uri, image):
    """
    Write a numpy array as an image or animated image.
    """
    path = _normalize_path(uri)
    arr = np.asarray(image)
    arr = _ensure_uint8(arr)
    fmt = _guess_format_from_path(path)

    if _is_single_image_shape(arr.shape):
        # Single image
        pil_img = _to_pil_image(arr)
        pil_img.save(path, format=fmt)
    elif _is_animated_shape(arr.shape):
        # Animated image (GIF)
        if arr.ndim == 3:
            # (N, H, W) -> grayscale frames
            frames = [Image.fromarray(frame, mode="L") for frame in arr]
        elif arr.ndim == 4:
            # (N, H, W, C)
            if arr.shape[3] == 1:
                frames = [Image.fromarray(frame[..., 0], mode="L") for frame in arr]
            elif arr.shape[3] == 3:
                frames = [Image.fromarray(frame, mode="RGB") for frame in arr]
            else:
                raise ValueError(f"Unsupported channel count: {arr.shape[3]}")
        else:
            raise ValueError(f"Unsupported array shape for animated image: {arr.shape}")

        # Save as GIF
        frames[0].save(
            path,
            save_all=True,
            append_images=frames[1:],
            loop=0,
            format="GIF",
            duration=40,  # default 25 fps
            disposal=2,
        )
    else:
        raise ValueError(f"Unsupported array shape for imwrite: {arr.shape}")

def imread(uri):
    """
    Read an image from disk and return as numpy array.
    For animated images, returns the first frame.
    """
    path = _normalize_path(uri)
    with Image.open(path) as img:
        # For animated images, return first frame
        img.seek(0)
        arr = np.array(img)
        # If grayscale, arr.shape == (H, W)
        # If RGB, arr.shape == (H, W, 3)
        return arr

def imiter(uri) -> Iterator[np.ndarray]:
    """
    Iterate over frames in an image (animated or static).
    For static images, yields a single frame.
    """
    path = _normalize_path(uri)
    with Image.open(path) as img:
        for frame in ImageSequence.Iterator(img):
            arr = np.array(frame)
            yield arr

class _Props:
    def __init__(self, shape, dtype):
        self.shape = shape
        self.dtype = dtype

def improps(uri):
    """
    Return an object with .shape and .dtype attributes for the image.
    For animated images, .shape is (N, H, W) or (N, H, W, C).
    """
    path = _normalize_path(uri)
    with Image.open(path) as img:
        n_frames = getattr(img, "n_frames", 1)
        mode = img.mode
        size = img.size  # (W, H)
        dtype = np.dtype("uint8")
        if n_frames == 1:
            # Static image
            if mode == "L":
                shape = (size[1], size[0])
            elif mode == "RGB":
                shape = (size[1], size[0], 3)
            else:
                # Try to convert to RGB
                arr = np.array(img.convert("RGB"))
                shape = arr.shape
        else:
            # Animated image
            # Read first frame to determine shape
            img.seek(0)
            arr0 = np.array(img)
            if arr0.ndim == 2:
                shape = (n_frames, arr0.shape[0], arr0.shape[1])
            elif arr0.ndim == 3:
                shape = (n_frames, arr0.shape[0], arr0.shape[1], arr0.shape[2])
            else:
                raise ValueError("Unknown frame shape in animated image.")
        return _Props(shape, dtype)

def immeta(uri) -> Dict[str, Any]:
    """
    Return a dict with at least a 'mode' key describing the image mode.
    """
    path = _normalize_path(uri)
    with Image.open(path) as img:
        meta = {}
        meta["mode"] = img.mode
        # Optionally add more keys if needed
        return meta