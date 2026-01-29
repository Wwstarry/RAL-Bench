# Pure-Python minimal image I/O compatible with a subset of Imageio v3
# Supports PNG single images and GIF animated images for uint8 arrays.

import io
import os
import struct
import zlib
import binascii
import pathlib
from typing import Iterable, Generator, Tuple, Dict, Any

import numpy as np


class ImageProps:
    """Simple container for image properties."""
    def __init__(self, shape: Tuple[int, ...], dtype: np.dtype):
        self.shape = tuple(shape)
        self.dtype = np.dtype(dtype)


def _ensure_path(uri) -> str:
    if isinstance(uri, pathlib.Path):
        return str(uri)
    elif isinstance(uri, (str, bytes)):
        return os.fspath(uri)
    else:
        raise TypeError("uri must be a str, bytes, or pathlib.Path")


def _is_png(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            sig = f.read(8)
        return sig == b"\x89PNG\r\n\x1a\n"
    except Exception:
        return False


def _is_gif(path: str) -> bool:
    try:
        with open(path, "rb") as f:
            sig = f.read(6)
        return sig in (b"GIF87a", b"GIF89a")
    except Exception:
        return False


def imwrite(uri, image):
    """Write image or animated image based on array shape and file extension."""
    path = _ensure_path(uri)
    arr = np.asarray(image)
    if arr.dtype != np.uint8:
        # For simplicity, only support uint8. Cast with clipping if needed.
        arr = arr.astype(np.uint8)

    # Normalize shapes
    if arr.ndim == 2:
        # Single grayscale
        if path.lower().endswith(".gif"):
            # Write single-frame GIF
            _write_gif(path, [arr])
        else:
            _write_png(path, arr)
    elif arr.ndim == 3:
        H, W, C = arr.shape
        if C in (1, 3):
            # Single image
            if path.lower().endswith(".gif"):
                # Write single-frame GIF (convert to grayscale if necessary)
                if C == 3:
                    gray = _rgb_to_gray(arr)
                else:
                    gray = arr[..., 0]
                _write_gif(path, [gray])
            else:
                _write_png(path, arr)
        else:
            # Assume animated grayscale stack (N, H, W)
            N, H, W = arr.shape
            frames = [arr[i] for i in range(N)]
            _write_gif(path, frames)
    elif arr.ndim == 4:
        N, H, W, C = arr.shape
        if C == 1:
            frames = [arr[i, :, :, 0] for i in range(N)]
        elif C == 3:
            # Convert RGB to grayscale for GIF
            frames = [_rgb_to_gray(arr[i]) for i in range(N)]
        else:
            raise ValueError("Unsupported number of channels for animated image.")
        _write_gif(path, frames)
    else:
        raise ValueError("Unsupported array shape for writing.")


def imread(uri):
    """Read image from a path; for GIF returns the first frame."""
    path = _ensure_path(uri)
    if _is_png(path):
        return _read_png(path)
    elif _is_gif(path):
        # Return the first frame
        for frame in _gif_iterate_frames(path):
            return frame
        raise ValueError("GIF contains no frames")
    else:
        # Try extension fallback
        if path.lower().endswith(".png"):
            return _read_png(path)
        elif path.lower().endswith(".gif"):
            for frame in _gif_iterate_frames(path):
                return frame
            raise ValueError("GIF contains no frames")
        else:
            raise ValueError("Unknown image file format.")


def imiter(uri) -> Iterable[np.ndarray]:
    """Return an iterable over frames of the image at the given path."""
    path = _ensure_path(uri)
    if _is_gif(path) or path.lower().endswith(".gif"):
        return _gif_iterate_frames(path)
    else:
        # For non-animated images, return a generator yielding a single frame
        def _single():
            yield imread(path)
        return _single()


def improps(uri) -> ImageProps:
    """Return basic properties describing the shape and dtype."""
    path = _ensure_path(uri)
    if _is_png(path) or path.lower().endswith(".png"):
        width, height, color_type, bit_depth = _png_read_ihdr(path)
        if bit_depth != 8 or color_type not in (0, 2):
            # Minimal support only
            raise ValueError("Unsupported PNG bit depth or color type.")
        if color_type == 0:
            shape = (height, width)
        elif color_type == 2:
            shape = (height, width, 3)
        else:
            shape = (height, width)
        return ImageProps(shape=shape, dtype=np.uint8)
    elif _is_gif(path) or path.lower().endswith(".gif"):
        width, height, nframes = _gif_props(path)
        # We represent GIF frames as grayscale 2D arrays
        shape = (nframes, height, width) if nframes > 1 else (height, width)
        return ImageProps(shape=shape, dtype=np.uint8)
    else:
        raise ValueError("Unknown image file format.")


def immeta(uri) -> Dict[str, Any]:
    """Return format-specific metadata; must include a 'mode' string."""
    path = _ensure_path(uri)
    if _is_png(path) or path.lower().endswith(".png"):
        _, _, color_type, _ = _png_read_ihdr(path)
        mode = "L" if color_type == 0 else "RGB" if color_type == 2 else "Unknown"
        return {"mode": mode}
    elif _is_gif(path) or path.lower().endswith(".gif"):
        # We write grayscale palette GIFs
        return {"mode": "P"}
    else:
        return {"mode": "Unknown"}


# ======================= PNG Implementation =======================

def _png_write_chunk(f, chunk_type: bytes, data: bytes):
    # length: 4-byte big-endian
    f.write(struct.pack(">I", len(data)))
    f.write(chunk_type)
    f.write(data)
    crc = binascii.crc32(chunk_type)
    crc = binascii.crc32(data, crc)
    f.write(struct.pack(">I", crc & 0xFFFFFFFF))


def _write_png(path: str, arr: np.ndarray):
    arr = np.asarray(arr)
    if arr.dtype != np.uint8:
        arr = arr.astype(np.uint8)

    if arr.ndim == 2:
        height, width = arr.shape
        color_type = 0  # grayscale
        bpp = 1
        raw_rows = []
        for y in range(height):
            row = arr[y].tobytes()
            raw_rows.append(b"\x00" + row)  # filter: None
    elif arr.ndim == 3 and arr.shape[2] in (1, 3):
        height, width, channels = arr.shape
        if channels == 1:
            arr = arr[:, :, 0]
            color_type = 0
            bpp = 1
            raw_rows = []
            for y in range(height):
                row = arr[y].tobytes()
                raw_rows.append(b"\x00" + row)
        else:
            color_type = 2  # RGB
            bpp = 3
            raw_rows = []
            # Ensure C-order bytes properly contiguous
            for y in range(height):
                row = arr[y].tobytes()
                raw_rows.append(b"\x00" + row)
    else:
        raise ValueError("Unsupported PNG shape. Use (H,W) or (H,W,3).")

    # Compose PNG file
    with open(path, "wb") as f:
        # PNG signature
        f.write(b"\x89PNG\r\n\x1a\n")
        # IHDR
        bit_depth = 8
        ihdr = struct.pack(">IIBBBBB",
                           width, height, bit_depth, color_type,
                           0, 0, 0)  # compression, filter, interlace = 0
        _png_write_chunk(f, b"IHDR", ihdr)
        # IDAT
        compressed = zlib.compress(b"".join(raw_rows))
        _png_write_chunk(f, b"IDAT", compressed)
        # IEND
        _png_write_chunk(f, b"IEND", b"")


def _png_read_ihdr(path: str) -> Tuple[int, int, int, int]:
    with open(path, "rb") as f:
        sig = f.read(8)
        if sig != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Not a PNG file.")
        # read chunks until IHDR read
        # After sig, next chunk should be IHDR
        data_len = struct.unpack(">I", f.read(4))[0]
        ctype = f.read(4)
        if ctype != b"IHDR":
            raise ValueError("Missing IHDR chunk.")
        data = f.read(data_len)
        f.read(4)  # skip CRC
        width, height, bit_depth, color_type, comp, filt, interlace = struct.unpack(">IIBBBBB", data)
        return width, height, color_type, bit_depth


def _read_png(path: str) -> np.ndarray:
    with open(path, "rb") as f:
        sig = f.read(8)
        if sig != b"\x89PNG\r\n\x1a\n":
            raise ValueError("Not a PNG file.")
        width = height = None
        bit_depth = None
        color_type = None
        idat_data = []
        # Parse chunks
        while True:
            length_bytes = f.read(4)
            if not length_bytes:
                break
            length = struct.unpack(">I", length_bytes)[0]
            ctype = f.read(4)
            data = f.read(length)
            crc = f.read(4)
            if ctype == b"IHDR":
                width, height, bit_depth, color_type, comp, filt, interlace = struct.unpack(">IIBBBBB", data)
                if comp != 0 or filt != 0 or interlace != 0:
                    raise ValueError("Unsupported PNG compression/filter/interlace.")
                if bit_depth != 8 or color_type not in (0, 2):
                    raise ValueError("Unsupported PNG format.")
            elif ctype == b"IDAT":
                idat_data.append(data)
            elif ctype == b"IEND":
                break
            else:
                # Ignore other chunks
                pass
        if width is None or not idat_data:
            raise ValueError("Invalid PNG: missing essential chunks.")
        decompressed = zlib.decompress(b"".join(idat_data))
        # Each scanline starts with a filter byte (we only support filter 0)
        if color_type == 0:
            bpp = 1
            row_size = 1 + width * bpp
            arr = np.empty((height, width), dtype=np.uint8)
            offset = 0
            for y in range(height):
                b = decompressed[offset]
                if b != 0:
                    raise ValueError("Unsupported PNG filter encountered.")
                row = decompressed[offset + 1: offset + row_size]
                arr[y] = np.frombuffer(row, dtype=np.uint8, count=width)
                offset += row_size
            return arr
        elif color_type == 2:
            bpp = 3
            row_size = 1 + width * bpp
            arr = np.empty((height, width, 3), dtype=np.uint8)
            offset = 0
            for y in range(height):
                b = decompressed[offset]
                if b != 0:
                    raise ValueError("Unsupported PNG filter encountered.")
                row = decompressed[offset + 1: offset + row_size]
                arr[y] = np.frombuffer(row, dtype=np.uint8, count=width * 3).reshape((width, 3))
                offset += row_size
            return arr
        else:
            raise ValueError("Unsupported PNG color type.")


# ======================= GIF Implementation =======================

def _rgb_to_gray(rgb: np.ndarray) -> np.ndarray:
    # Simple luminance approximation, result dtype uint8
    rgb = rgb.astype(np.uint8)
    # Use weighted average to approximate luminosity
    r = rgb[..., 0].astype(np.float32)
    g = rgb[..., 1].astype(np.float32)
    b = rgb[..., 2].astype(np.float32)
    gray = (0.299 * r + 0.587 * g + 0.114 * b).round().astype(np.uint8)
    return gray


def _write_gif(path: str, frames: Iterable[np.ndarray]):
    # frames: list of 2D uint8 arrays
    frames = list(frames)
    if not frames:
        raise ValueError("No frames to write.")
    H, W = frames[0].shape
    # Ensure all frames same size and dtype
    processed_frames = []
    for f in frames:
        a = np.asarray(f)
        if a.dtype != np.uint8:
            a = a.astype(np.uint8)
        if a.ndim != 2:
            raise ValueError("GIF frames must be 2D arrays (grayscale indices).")
        if a.shape != (H, W):
            raise ValueError("All GIF frames must have the same shape.")
        processed_frames.append(a)

    with open(path, "wb") as fp:
        # Header
        fp.write(b"GIF89a")
        # Logical Screen Descriptor
        # Packed fields: GCT flag=1, color resolution=7, sort=0, GCT size=7 (256 colors)
        packed = (1 << 7) | (7 << 4) | (0 << 3) | 7
        fp.write(struct.pack("<HHBBB", W, H, packed, 0, 0))
        # Global Color Table: grayscale 256
        gct = bytearray()
        for i in range(256):
            gct += bytes((i, i, i))
        fp.write(gct)
        # Netscape application extension for looping
        fp.write(b"\x21\xFF\x0B" + b"NETSCAPE2.0")
        # Sub-block: size 3, data: 1 + loops(lo, hi) where 0 indicates infinite loops
        fp.write(b"\x03\x01\x00\x00\x00")

        # Write each frame
        for frame in processed_frames:
            # Graphics Control Extension: 0 delay, no transparency
            fp.write(b"\x21\xF9\x04\x00\x00\x00\x00\x00")
            # Image Descriptor
            # No local color table, non-interlaced
            fp.write(b"\x2C" + struct.pack("<HHHHB", 0, 0, W, H, 0))
            # LZW minimum code size (8 for 8-bit indices)
            fp.write(b"\x08")
            # Encode pixels row-major
            data = frame.tobytes(order="C")
            lzw_bytes = _lzw_encode(data, min_code_size=8)
            # Write as sub-blocks of up to 255 bytes
            pos = 0
            total = len(lzw_bytes)
            while pos < total:
                chunk = lzw_bytes[pos: pos + 255]
                fp.write(bytes((len(chunk),)))
                fp.write(chunk)
                pos += len(chunk)
            # Block terminator
            fp.write(b"\x00")
        # Trailer
        fp.write(b"\x3B")


def _lzw_encode(data: bytes, min_code_size: int = 8) -> bytes:
    # GIF LZW encoder with clear/end codes and code-size growth up to 12 bits.
    clear_code = 1 << min_code_size  # 256
    end_code = clear_code + 1        # 257
    next_code = end_code + 1         # 258
    code_size = min_code_size + 1    # start at 9
    max_code = (1 << code_size) - 1

    # Initialize dictionary
    dictionary = {bytes([i]): i for i in range(clear_code)}

    # Bitstream buffer (LSB-first)
    out_bytes = bytearray()
    bit_buffer = 0
    bit_count = 0

    def write_code(code: int):
        nonlocal bit_buffer, bit_count, out_bytes
        bit_buffer |= (code & ((1 << code_size) - 1)) << bit_count
        bit_count += code_size
        while bit_count >= 8:
            out_bytes.append(bit_buffer & 0xFF)
            bit_buffer >>= 8
            bit_count -= 8

    # Start with clear code
    write_code(clear_code)

    w = b""
    for k in data:
        k_bytes = bytes([k])
        wk = w + k_bytes
        if wk in dictionary:
            w = wk
        else:
            # Output code for w
            write_code(dictionary[w] if w else k)
            # Add wk to dictionary
            dictionary[wk] = next_code
            next_code += 1
            # Increase code size if needed
            if next_code > max_code and code_size < 12:
                code_size += 1
                max_code = (1 << code_size) - 1
            elif next_code >= 4096:
                # Dictionary full; emit clear and reset
                write_code(clear_code)
                dictionary = {bytes([i]): i for i in range(clear_code)}
                next_code = end_code + 1
                code_size = min_code_size + 1
                max_code = (1 << code_size) - 1
            w = k_bytes
    if w:
        write_code(dictionary[w])
    # End code
    write_code(end_code)
    # Flush remaining bits
    if bit_count > 0:
        out_bytes.append(bit_buffer & 0xFF)
    return bytes(out_bytes)


def _read_subblocks(fp) -> bytes:
    """Read GIF sub-blocks into a single bytes object."""
    chunks = bytearray()
    while True:
        sz_b = fp.read(1)
        if not sz_b:
            break
        sz = sz_b[0]
        if sz == 0:
            break
        data = fp.read(sz)
        if len(data) != sz:
            break
        chunks.extend(data)
    return bytes(chunks)


def _gif_iterate_frames(path: str) -> Generator[np.ndarray, None, None]:
    with open(path, "rb") as fp:
        header = fp.read(6)
        if header not in (b"GIF87a", b"GIF89a"):
            raise ValueError("Not a GIF file.")
        # Logical Screen Descriptor
        ls = fp.read(7)
        W, H, packed, bg, aspect = struct.unpack("<HHBBB", ls)
        gct_flag = (packed & 0x80) >> 7
        gct_size_value = packed & 0x07
        gct_size = 2 ** (gct_size_value + 1)
        if gct_flag:
            fp.read(3 * gct_size)
        # Iterate blocks
        while True:
            introducer = fp.read(1)
            if not introducer:
                break
            b = introducer[0]
            if b == 0x3B:
                # Trailer
                break
            elif b == 0x21:
                # Extension
                label = fp.read(1)
                if not label:
                    break
                if label[0] == 0xF9:
                    # Graphics Control Extension
                    block_size_b = fp.read(1)
                    if not block_size_b:
                        break
                    block_size = block_size_b[0]
                    data = fp.read(block_size)
                    fp.read(1)  # block terminator
                else:
                    # Application or other extension: read data sub-blocks
                    # First block may be application ID length (usually 11)
                    # Read until terminator
                    # Read a block size; if zero then done
                    # We already read label; now read subblocks generically
                    # Possibly there is a fixed-length initial block for APP
                    # We'll consume in generic fashion
                    # Read sub-blocks (size, data) until sz==0
                    # First we may have an initial block size preceding sub-blocks
                    # We'll handle generically:
                    # Read blocks until terminator
                    _ = _read_subblocks(fp)
            elif b == 0x2C:
                # Image Descriptor
                idesc = fp.read(9)
                left, top, width, height, ipacked = struct.unpack("<HHHHB", idesc)
                lct_flag = (ipacked & 0x80) >> 7
                interlace_flag = (ipacked & 0x40) >> 6
                lct_size_value = ipacked & 0x07
                if lct_flag:
                    lct_size = 2 ** (lct_size_value + 1)
                    fp.read(3 * lct_size)
                # LZW minimum code size
                lzw_min_b = fp.read(1)
                if not lzw_min_b:
                    break
                lzw_min_code_size = lzw_min_b[0]
                # Image data
                data_stream = _read_subblocks(fp)
                # Decode
                pixels = _lzw_decode(data_stream, lzw_min_code_size)
                # Expect width*height bytes
                if len(pixels) < width * height:
                    # Some encoders might store interlaced data; we don't support.
                    raise ValueError("Unsupported GIF interlace or truncated data.")
                # Construct frame
                arr = np.frombuffer(pixels[: width * height], dtype=np.uint8).reshape((height, width))
                yield arr
            else:
                # Unknown; stop
                break


def _lzw_decode(data: bytes, min_code_size: int) -> bytes:
    # Decode LZW packed bit stream (LSB-first) into bytes
    clear_code = 1 << min_code_size
    end_code = clear_code + 1
    next_code = end_code + 1
    code_size = min_code_size + 1

    # Initialize dictionary
    dictionary = {i: bytes([i]) for i in range(clear_code)}

    # Bitstream reader (LSB-first)
    class BitReader:
        def __init__(self, data: bytes):
            self.data = data
            self.pos = 0  # byte position
            self.bit_pos = 0  # bit position in current byte

        def read(self, nbits: int) -> int:
            val = 0
            shift = 0
            while nbits > 0:
                if self.pos >= len(self.data):
                    raise EOFError("Unexpected end of LZW data.")
                remain_in_byte = 8 - self.bit_pos
                take = min(remain_in_byte, nbits)
                byte = self.data[self.pos]
                bits = (byte >> self.bit_pos) & ((1 << take) - 1)
                val |= bits << shift
                self.bit_pos += take
                if self.bit_pos >= 8:
                    self.pos += 1
                    self.bit_pos = 0
                nbits -= take
                shift += take
            return val

    br = BitReader(data)
    out = bytearray()

    # Read first code (should be clear)
    try:
        code = br.read(code_size)
    except EOFError:
        return bytes(out)
    if code != clear_code:
        # Some encoders may not start with clear, but we assume ours does
        # We'll treat as clear anyway
        pass

    # Reset dictionary.
    dictionary = {i: bytes([i]) for i in range(clear_code)}
    next_code = end_code + 1
    code_size = min_code_size + 1
    prev_seq = b""

    while True:
        try:
            code = br.read(code_size)
        except EOFError:
            break
        if code == clear_code:
            # Reset
            dictionary = {i: bytes([i]) for i in range(clear_code)}
            next_code = end_code + 1
            code_size = min_code_size + 1
            # Read next code to start new sequence
            try:
                code = br.read(code_size)
            except EOFError:
                break
            if code == end_code:
                break
            seq = dictionary.get(code, b"")
            out.extend(seq)
            prev_seq = seq
            continue
        if code == end_code:
            break

        if code in dictionary:
            seq = dictionary[code]
        elif code == next_code and prev_seq:
            # Special case
            seq = prev_seq + prev_seq[:1]
        else:
            # Malformed stream
            seq = b""
        if seq:
            out.extend(seq)
            if prev_seq:
                dictionary[next_code] = prev_seq + seq[:1]
                next_code += 1
                if next_code == (1 << code_size) and code_size < 12:
                    code_size += 1
            prev_seq = seq
        else:
            break

    return bytes(out)


def _gif_props(path: str) -> Tuple[int, int, int]:
    """Return (width, height, nframes) for GIF without decoding."""
    nframes = 0
    with open(path, "rb") as fp:
        header = fp.read(6)
        if header not in (b"GIF87a", b"GIF89a"):
            raise ValueError("Not a GIF file.")
        ls = fp.read(7)
        W, H, packed, bg, aspect = struct.unpack("<HHBBB", ls)
        gct_flag = (packed & 0x80) >> 7
        gct_size_value = packed & 0x07
        gct_size = 2 ** (gct_size_value + 1)
        if gct_flag:
            fp.read(3 * gct_size)
        # Iterate blocks and count image descriptors
        while True:
            introducer = fp.read(1)
            if not introducer:
                break
            b = introducer[0]
            if b == 0x3B:
                break
            elif b == 0x21:
                # Extension: skip
                label = fp.read(1)
                if not label:
                    break
                if label[0] == 0xF9:
                    # Graphics Control Extension
                    blk_size_b = fp.read(1)
                    if not blk_size_b:
                        break
                    blk_size = blk_size_b[0]
                    fp.read(blk_size)
                    fp.read(1)  # terminator
                else:
                    # Generic sub-blocks
                    _ = _read_subblocks(fp)
            elif b == 0x2C:
                # Image Descriptor
                idesc = fp.read(9)
                _, _, width, height, ipacked = struct.unpack("<HHHHB", idesc)
                lct_flag = (ipacked & 0x80) >> 7
                lct_size_value = ipacked & 0x07
                if lct_flag:
                    lct_size = 2 ** (lct_size_value + 1)
                    fp.read(3 * lct_size)
                # Skip LZW stream
                lzw_min_b = fp.read(1)
                if not lzw_min_b:
                    break
                _ = _read_subblocks(fp)
                nframes += 1
            else:
                # Unknown; stop
                break
    return (W, H, nframes)


# ======================= End of implementation =======================