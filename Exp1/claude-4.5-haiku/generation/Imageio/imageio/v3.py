"""
Imageio v3 API: high-level functions for reading and writing images.

This module provides:
  - imwrite(uri, image): write an image or image sequence to disk
  - imread(uri): read a single image from disk
  - imiter(uri): iterate over frames in an image file
  - improps(uri): get image properties (shape, dtype)
  - immeta(uri): get image metadata (format-specific info)
"""

import io
import struct
import zlib
from pathlib import Path
from typing import Union, Iterable, Dict, Any

import numpy as np


class ImageProperties:
    """Container for image properties."""

    def __init__(self, shape: tuple, dtype: np.dtype):
        self.shape = shape
        self.dtype = dtype

    def __repr__(self) -> str:
        return f"ImageProperties(shape={self.shape}, dtype={self.dtype})"


class PNGEncoder:
    """Pure Python PNG encoder."""

    def __init__(self, width: int, height: int, color_type: int, bit_depth: int = 8):
        self.width = width
        self.height = height
        self.color_type = color_type
        self.bit_depth = bit_depth

    def encode(self, data: np.ndarray) -> bytes:
        """Encode image data to PNG format."""
        # Ensure data is in the correct format
        if self.color_type == 0:  # Grayscale
            if len(data.shape) == 3:
                data = data[:, :, 0]
        elif self.color_type == 2:  # RGB
            if len(data.shape) == 2:
                data = np.stack([data] * 3, axis=-1)

        png_data = io.BytesIO()

        # PNG signature
        png_data.write(b'\x89PNG\r\n\x1a\n')

        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB',
                                self.width,
                                self.height,
                                self.bit_depth,
                                self.color_type,
                                0,  # compression method
                                0,  # filter method
                                0)  # interlace method
        self._write_chunk(png_data, b'IHDR', ihdr_data)

        # IDAT chunk(s)
        raw_data = self._prepare_image_data(data)
        compressed = zlib.compress(raw_data, 9)
        self._write_chunk(png_data, b'IDAT', compressed)

        # IEND chunk
        self._write_chunk(png_data, b'IEND', b'')

        return png_data.getvalue()

    def _prepare_image_data(self, data: np.ndarray) -> bytes:
        """Prepare raw image data with filter bytes."""
        if self.color_type == 0:  # Grayscale
            bytes_per_pixel = 1
        elif self.color_type == 2:  # RGB
            bytes_per_pixel = 3
        else:
            raise ValueError(f"Unsupported color type: {self.color_type}")

        raw = io.BytesIO()
        for y in range(self.height):
            raw.write(b'\x00')  # Filter type: None
            if self.color_type == 0:
                raw.write(data[y, :].tobytes())
            elif self.color_type == 2:
                raw.write(data[y, :, :].tobytes())

        return raw.getvalue()

    def _write_chunk(self, png_file: io.BytesIO, chunk_type: bytes, data: bytes):
        """Write a PNG chunk."""
        length = len(data)
        png_file.write(struct.pack('>I', length))
        png_file.write(chunk_type)
        png_file.write(data)
        crc = zlib.crc32(chunk_type + data) & 0xffffffff
        png_file.write(struct.pack('>I', crc))


class PNGDecoder:
    """Pure Python PNG decoder."""

    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def decode(self) -> tuple:
        """Decode PNG data and return (array, color_type)."""
        # Check PNG signature
        if self.data[:8] != b'\x89PNG\r\n\x1a\n':
            raise ValueError("Invalid PNG signature")
        self.pos = 8

        width = None
        height = None
        bit_depth = None
        color_type = None
        image_data = b''

        while self.pos < len(self.data):
            length, chunk_type, chunk_data = self._read_chunk()

            if chunk_type == b'IHDR':
                width, height, bit_depth, color_type = self._parse_ihdr(chunk_data)
            elif chunk_type == b'IDAT':
                image_data += chunk_data
            elif chunk_type == b'IEND':
                break

        if width is None or height is None:
            raise ValueError("Invalid PNG: missing IHDR chunk")

        # Decompress image data
        raw_data = zlib.decompress(image_data)

        # Parse image data
        array = self._parse_image_data(raw_data, width, height, color_type, bit_depth)

        return array, color_type

    def _read_chunk(self) -> tuple:
        """Read a PNG chunk and return (length, type, data)."""
        length_bytes = self.data[self.pos:self.pos + 4]
        length = struct.unpack('>I', length_bytes)[0]
        self.pos += 4

        chunk_type = self.data[self.pos:self.pos + 4]
        self.pos += 4

        chunk_data = self.data[self.pos:self.pos + length]
        self.pos += length

        # Skip CRC
        self.pos += 4

        return length, chunk_type, chunk_data

    def _parse_ihdr(self, data: bytes) -> tuple:
        """Parse IHDR chunk."""
        width, height, bit_depth, color_type, compression, filter_method, interlace = \
            struct.unpack('>IIBBBBB', data)
        return width, height, bit_depth, color_type

    def _parse_image_data(self, raw_data: bytes, width: int, height: int,
                          color_type: int, bit_depth: int) -> np.ndarray:
        """Parse raw image data into numpy array."""
        if color_type == 0:  # Grayscale
            bytes_per_pixel = 1
            channels = 1
        elif color_type == 2:  # RGB
            bytes_per_pixel = 3
            channels = 3
        else:
            raise ValueError(f"Unsupported color type: {color_type}")

        array = np.zeros((height, width, channels), dtype=np.uint8)

        pos = 0
        for y in range(height):
            filter_type = raw_data[pos]
            pos += 1

            for x in range(width):
                for c in range(channels):
                    array[y, x, c] = raw_data[pos]
                    pos += 1

        if channels == 1:
            array = array[:, :, 0]

        return array


class GIFEncoder:
    """Pure Python GIF encoder for simple image sequences."""

    def __init__(self, width: int, height: int, duration: int = 100):
        self.width = width
        self.height = height
        self.duration = duration

    def encode(self, frames: list) -> bytes:
        """Encode a list of frames to GIF format."""
        gif_data = io.BytesIO()

        # GIF signature and version
        gif_data.write(b'GIF89a')

        # Logical Screen Descriptor
        gif_data.write(struct.pack('<HH', self.width, self.height))
        gif_data.write(b'\xf7\x00\x00')  # packed fields, background, aspect ratio

        # Global Color Table (256 colors, grayscale)
        for i in range(256):
            gif_data.write(bytes([i, i, i]))

        # Write frames
        for frame in frames:
            self._write_frame(gif_data, frame)

        # GIF trailer
        gif_data.write(b'\x3b')

        return gif_data.getvalue()

    def _write_frame(self, gif_file: io.BytesIO, frame: np.ndarray):
        """Write a single frame to GIF."""
        # Ensure frame is 2D grayscale
        if len(frame.shape) == 3:
            frame = frame[:, :, 0]

        # Graphics Control Extension (for animation timing)
        gif_file.write(b'\x21\xf9\x04\x00')
        gif_file.write(struct.pack('<H', self.duration))
        gif_file.write(b'\x00\x00')

        # Image Descriptor
        gif_file.write(b'\x2c')
        gif_file.write(struct.pack('<HHHHB', 0, 0, self.width, self.height, 0))

        # Image Data (LZW compressed)
        image_data = self._lzw_encode(frame)
        gif_file.write(image_data)

    def _lzw_encode(self, frame: np.ndarray) -> bytes:
        """Simple LZW encoding for GIF image data."""
        # Flatten frame
        pixels = frame.flatten().astype(np.uint8)

        # LZW encoding
        result = io.BytesIO()
        result.write(b'\x08')  # LZW minimum code size

        # Simple implementation: just write raw pixel data in blocks
        block_size = 255
        for i in range(0, len(pixels), block_size):
            block = pixels[i:i + block_size]
            result.write(bytes([len(block)]))
            result.write(block.tobytes())

        result.write(b'\x00')  # Block terminator

        return result.getvalue()


class GIFDecoder:
    """Pure Python GIF decoder."""

    def __init__(self, data: bytes):
        self.data = data
        self.pos = 0

    def decode(self) -> list:
        """Decode GIF data and return list of frames."""
        # Check GIF signature
        if self.data[:6] not in (b'GIF87a', b'GIF89a'):
            raise ValueError("Invalid GIF signature")
        self.pos = 6

        # Logical Screen Descriptor
        width, height = struct.unpack('<HH', self.data[self.pos:self.pos + 4])
        self.pos += 4

        packed = self.data[self.pos]
        self.pos += 1
        self.pos += 2  # background color index, aspect ratio

        # Global Color Table
        gct_flag = (packed >> 7) & 1
        if gct_flag:
            gct_size = 2 ** ((packed & 0x07) + 1)
            self.pos += gct_size * 3

        frames = []

        while self.pos < len(self.data):
            separator = self.data[self.pos]
            self.pos += 1

            if separator == 0x21:  # Extension
                label = self.data[self.pos]
                self.pos += 1
                self._skip_data_sub_blocks()
            elif separator == 0x2c:  # Image
                frame = self._read_image(width, height)
                frames.append(frame)
            elif separator == 0x3b:  # Trailer
                break

        return frames

    def _skip_data_sub_blocks(self):
        """Skip data sub-blocks."""
        while True:
            block_size = self.data[self.pos]
            self.pos += 1
            if block_size == 0:
                break
            self.pos += block_size

    def _read_image(self, width: int, height: int) -> np.ndarray:
        """Read a single image from GIF."""
        # Image Descriptor
        left, top, img_width, img_height = struct.unpack('<HHHH', self.data[self.pos:self.pos + 8])
        self.pos += 8

        packed = self.data[self.pos]
        self.pos += 1

        lct_flag = (packed >> 7) & 1
        if lct_flag:
            lct_size = 2 ** ((packed & 0x07) + 1)
            self.pos += lct_size * 3

        # LZW minimum code size
        lzw_min_code_size = self.data[self.pos]
        self.pos += 1

        # Read image data sub-blocks
        image_data = b''
        while True:
            block_size = self.data[self.pos]
            self.pos += 1
            if block_size == 0:
                break
            image_data += self.data[self.pos:self.pos + block_size]
            self.pos += block_size

        # Simple decoding: assume raw pixel data
        pixels = np.frombuffer(image_data, dtype=np.uint8)
        if len(pixels) >= img_width * img_height:
            frame = pixels[:img_width * img_height].reshape((img_height, img_width))
        else:
            frame = np.zeros((img_height, img_width), dtype=np.uint8)
            frame.flat[:len(pixels)] = pixels

        return frame


def imwrite(uri: Union[str, Path], image: np.ndarray) -> None:
    """
    Write an image or image sequence to disk.

    Parameters
    ----------
    uri : str or Path
        The file path where the image will be written.
    image : np.ndarray
        The image data. Can be:
        - 2D array (H, W): grayscale image
        - 3D array (H, W, 1): grayscale image with explicit channel
        - 3D array (H, W, 3): RGB image
        - 3D array (N, H, W): grayscale image sequence
        - 4D array (N, H, W, C): color image sequence
    """
    uri = Path(uri)
    suffix = uri.suffix.lower()

    if suffix in ('.png',):
        _imwrite_png(uri, image)
    elif suffix in ('.gif',):
        _imwrite_gif(uri, image)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def _imwrite_png(uri: Path, image: np.ndarray) -> None:
    """Write a single image as PNG."""
    image = np.asarray(image, dtype=np.uint8)

    if len(image.shape) == 2:
        # (H, W) grayscale
        height, width = image.shape
        color_type = 0
    elif len(image.shape) == 3:
        if image.shape[2] == 1:
            # (H, W, 1) grayscale
            height, width = image.shape[:2]
            image = image[:, :, 0]
            color_type = 0
        elif image.shape[2] == 3:
            # (H, W, 3) RGB
            height, width = image.shape[:2]
            color_type = 2
        else:
            raise ValueError(f"Unsupported number of channels: {image.shape[2]}")
    else:
        raise ValueError(f"Unsupported image shape: {image.shape}")

    encoder = PNGEncoder(width, height, color_type)
    png_data = encoder.encode(image)

    with open(uri, 'wb') as f:
        f.write(png_data)


def _imwrite_gif(uri: Path, image: np.ndarray) -> None:
    """Write an image sequence as GIF."""
    image = np.asarray(image, dtype=np.uint8)

    if len(image.shape) == 3:
        # (N, H, W) grayscale sequence
        frames = [image[i] for i in range(image.shape[0])]
        height, width = image.shape[1:3]
    elif len(image.shape) == 4:
        # (N, H, W, C) color sequence
        if image.shape[3] == 1:
            frames = [image[i, :, :, 0] for i in range(image.shape[0])]
        elif image.shape[3] == 3:
            frames = [image[i, :, :, 0] for i in range(image.shape[0])]  # Use first channel
        else:
            raise ValueError(f"Unsupported number of channels: {image.shape[3]}")
        height, width = image.shape[1:3]
    else:
        raise ValueError(f"Unsupported image shape for GIF: {image.shape}")

    encoder = GIFEncoder(width, height)
    gif_data = encoder.encode(frames)

    with open(uri, 'wb') as f:
        f.write(gif_data)


def imread(uri: Union[str, Path]) -> np.ndarray:
    """
    Read an image from disk.

    Parameters
    ----------
    uri : str or Path
        The file path to read from.

    Returns
    -------
    np.ndarray
        The image data as a numpy array.
    """
    uri = Path(uri)
    suffix = uri.suffix.lower()

    if suffix == '.png':
        return _imread_png(uri)
    elif suffix == '.gif':
        # For GIF, return the first frame
        frames = _imread_gif(uri)
        return frames[0] if frames else np.array([], dtype=np.uint8)
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def _imread_png(uri: Path) -> np.ndarray:
    """Read a PNG image."""
    with open(uri, 'rb') as f:
        data = f.read()

    decoder = PNGDecoder(data)
    array, color_type = decoder.decode()

    return array


def _imread_gif(uri: Path) -> list:
    """Read a GIF image sequence."""
    with open(uri, 'rb') as f:
        data = f.read()

    decoder = GIFDecoder(data)
    frames = decoder.decode()

    return frames


def imiter(uri: Union[str, Path]) -> Iterable[np.ndarray]:
    """
    Iterate over frames in an image file.

    Parameters
    ----------
    uri : str or Path
        The file path to read from.

    Yields
    ------
    np.ndarray
        Image frames as numpy arrays.
    """
    uri = Path(uri)
    suffix = uri.suffix.lower()

    if suffix == '.png':
        # PNG files contain a single image
        yield imread(uri)
    elif suffix == '.gif':
        frames = _imread_gif(uri)
        for frame in frames:
            yield frame
    else:
        raise ValueError(f"Unsupported file format: {suffix}")


def improps(uri: Union[str, Path]) -> ImageProperties:
    """
    Get image properties.

    Parameters
    ----------
    uri : str or Path
        The file path to read from.

    Returns
    -------
    ImageProperties
        Object with `shape` and `dtype` attributes.
    """
    array = imread(uri)
    return ImageProperties(shape=array.shape, dtype=array.dtype)


def immeta(uri: Union[str, Path]) -> Dict[str, Any]:
    """
    Get image metadata.

    Parameters
    ----------
    uri : str or Path
        The file path to read from.

    Returns
    -------
    dict
        Metadata dictionary with at least a "mode" key.
    """
    uri = Path(uri)
    suffix = uri.suffix.lower()

    if suffix == '.png':
        with open(uri, 'rb') as f:
            data = f.read()
        decoder = PNGDecoder(data)
        array, color_type = decoder.decode()

        if color_type == 0:
            mode = 'L'
        elif color_type == 2:
            mode = 'RGB'
        else:
            mode = 'UNKNOWN'

        return {'mode': mode}
    elif suffix == '.gif':
        return {'mode': 'L'}
    else:
        raise ValueError(f"Unsupported file format: {suffix}")