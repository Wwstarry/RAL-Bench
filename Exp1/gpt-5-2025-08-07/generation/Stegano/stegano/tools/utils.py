from typing import List, Tuple, Union
from PIL import Image
from .bititerator import bytes_to_bits, bits_to_bytes

def ensure_image_mode(image: Image.Image, auto_convert_rgb: bool = False) -> Image.Image:
    """
    Ensure image mode is suitable for LSB operations.
    If auto_convert_rgb is True, convert to RGB if possible.
    Otherwise returns the image unchanged (for modes like L/LA/RGB/RGBA).
    """
    if auto_convert_rgb and image.mode not in ("RGB", "RGBA"):
        try:
            return image.convert("RGB")
        except Exception:
            return image
    # Keep as is; we can operate on L/LA/RGB/RGBA
    return image

def message_to_bytes(message: Union[str, bytes], encoding: str = "UTF-8") -> bytes:
    if isinstance(message, bytes):
        return message
    return str(message).encode(encoding, errors="strict")

def int_to_bits_be(value: int, width: int) -> List[int]:
    """
    Convert integer to big-endian bit list of given width.
    """
    if width <= 0:
        return []
    bits: List[int] = []
    for i in range(width - 1, -1, -1):
        bits.append((value >> i) & 1)
    return bits

def bits_to_int_be(bits: List[int]) -> int:
    """
    Convert list of bits (big-endian order) to integer.
    """
    acc = 0
    for bit in bits:
        acc = (acc << 1) | (bit & 1)
    return acc

def get_channel_indices(bands: Tuple[str, ...]) -> List[int]:
    """
    Return list of indices of usable channels (exclude alpha).
    For typical modes:
    - RGB: [0,1,2]
    - RGBA: [0,1,2]
    - L: [0]
    - LA: [0]
    """
    indices: List[int] = []
    for i, b in enumerate(bands):
        if b.upper() != "A":  # exclude alpha
            indices.append(i)
    # In some modes there might be no 'A', e.g., 'P' -> convert before call.
    # If no usable channels, return empty list.
    return indices

def image_pixels_as_tuples(image: Image.Image) -> List[Tuple[int, ...]]:
    """
    Return a list of pixel tuples for the given image.
    Ensures single-channel modes produce 1-length tuples for uniform processing.
    """
    pixels_raw = list(image.getdata())
    if not pixels_raw:
        return []
    first = pixels_raw[0]
    if isinstance(first, tuple):
        return [tuple(p) for p in pixels_raw]
    else:
        # Single-channel; wrap into 1-tuple
        return [(int(p),) for p in pixels_raw]

def put_pixels_from_tuples(image: Image.Image, pixels: List[Tuple[int, ...]]) -> None:
    """
    Put pixel tuples back into the image.
    Converts 1-length tuples back to ints for single-channel images.
    """
    if not pixels:
        return
    if len(pixels[0]) == 1:
        image.putdata([p[0] for p in pixels])
    else:
        image.putdata(pixels)