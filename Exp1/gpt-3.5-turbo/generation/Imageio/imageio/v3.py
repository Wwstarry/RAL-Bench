import numpy as np
from pathlib import Path
import struct

# Minimal PNG encoder and decoder for uint8 images (grayscale or RGB)
# Minimal GIF encoder and decoder for animated images (uint8, grayscale only or RGB)

# PNG constants
_PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'

def _crc32(data):
    import zlib
    return zlib.crc32(data) & 0xffffffff

def _write_png(path, arr):
    # arr: uint8 ndarray, shape (H,W) or (H,W,3)
    # Write a PNG file with no compression (filter type 0), no interlace.
    # Use color type 0 (grayscale) or 2 (RGB).
    arr = np.ascontiguousarray(arr)
    if arr.dtype != np.uint8:
        raise ValueError("Only uint8 arrays supported for PNG")
    if arr.ndim == 2:
        color_type = 0
        channels = 1
    elif arr.ndim == 3 and arr.shape[2] == 3:
        color_type = 2
        channels = 3
    elif arr.ndim == 3 and arr.shape[2] == 1:
        color_type = 0
        channels = 1
        arr = arr.reshape(arr.shape[0], arr.shape[1])
    else:
        raise ValueError("Unsupported shape for PNG write: %s" % (arr.shape,))
    height, width = arr.shape[:2]

    def pack_chunk(chunk_type, data):
        chunk = chunk_type + data
        length = struct.pack(">I", len(data))
        crc = struct.pack(">I", _crc32(chunk))
        return length + chunk + crc

    # IHDR chunk
    ihdr = struct.pack(">IIBBBBB",
                       width, height, 8, color_type, 0, 0, 0)
    # IDAT chunk: uncompressed zlib stream with filter bytes
    # We use zlib compression with default compression level.
    # Each scanline is preceded by a filter byte 0.
    raw = b""
    for row in arr:
        raw += b"\x00" + row.tobytes()
    import zlib
    compressed = zlib.compress(raw, level=6)

    with open(path, "wb") as f:
        f.write(_PNG_SIGNATURE)
        f.write(pack_chunk(b'IHDR', ihdr))
        f.write(pack_chunk(b'IDAT', compressed))
        f.write(pack_chunk(b'IEND', b''))

def _read_png(path):
    # Return ndarray uint8 with shape (H,W) or (H,W,3)
    with open(path, "rb") as f:
        sig = f.read(8)
        if sig != _PNG_SIGNATURE:
            raise ValueError("Not a PNG file")
        chunks = []
        while True:
            length_bytes = f.read(4)
            if len(length_bytes) < 4:
                break
            length = struct.unpack(">I", length_bytes)[0]
            chunk_type = f.read(4)
            data = f.read(length)
            crc = f.read(4)
            chunks.append((chunk_type, data))
            if chunk_type == b'IEND':
                break
    ihdr = None
    idat_data = b""
    for ctype, data in chunks:
        if ctype == b'IHDR':
            ihdr = data
        elif ctype == b'IDAT':
            idat_data += data
    if ihdr is None:
        raise ValueError("Missing IHDR chunk")
    width, height, bit_depth, color_type, compression, filter_method, interlace = struct.unpack(">IIBBBBB", ihdr)
    if bit_depth != 8:
        raise ValueError("Only 8-bit PNG supported")
    if compression != 0 or filter_method != 0 or interlace != 0:
        raise ValueError("Unsupported PNG compression/filter/interlace")
    import zlib
    raw = zlib.decompress(idat_data)
    # raw contains scanlines with filter byte 0
    # Each scanline: 1 filter byte + width*channels bytes
    if color_type == 0:
        channels = 1
    elif color_type == 2:
        channels = 3
    else:
        raise ValueError("Unsupported PNG color type %d" % color_type)
    expected_len = height * (1 + width * channels)
    if len(raw) != expected_len:
        raise ValueError("PNG decompressed data length mismatch")
    arr = np.empty((height, width, channels), dtype=np.uint8) if channels > 1 else np.empty((height, width), dtype=np.uint8)
    pos = 0
    for y in range(height):
        filter_type = raw[pos]
        if filter_type != 0:
            raise ValueError("Unsupported PNG filter type %d" % filter_type)
        pos += 1
        scanline = raw[pos:pos + width * channels]
        pos += width * channels
        if channels == 1:
            arr[y, :] = np.frombuffer(scanline, dtype=np.uint8)
        else:
            arr[y, :, :] = np.frombuffer(scanline, dtype=np.uint8).reshape((width, channels))
    return arr

# GIF encoder and decoder for animated images
# We only support writing and reading GIFs with 256 colors max, no transparency, no interlace.
# We convert RGB or grayscale frames to palette-based GIF.

def _rgb_to_palette_and_indices(frames):
    # frames: (N,H,W,3) uint8 or (N,H,W) uint8
    # Return palette (list of 768 bytes) and indices (N,H,W) uint8
    # Use a simple median cut quantizer or a fixed palette for speed.
    # For simplicity, use a fixed palette of 256 colors: 6x6x6 cube + grayscale ramp
    # This is a rough approximation but acceptable for tests.
    # Map RGB to nearest palette color.

    # Build palette: 6x6x6 cube (216 colors)
    palette = []
    for r in range(6):
        for g in range(6):
            for b in range(6):
                palette.extend([int(r * 255 / 5), int(g * 255 / 5), int(b * 255 / 5)])
    # Add 40 grayscale colors
    for i in range(40):
        v = int(i * 255 / 39)
        palette.extend([v, v, v])
    palette = palette[:768]  # 256*3

    palette_arr = np.array(palette, dtype=np.uint8).reshape((256, 3))

    # Flatten frames to (N*H*W, 3)
    if frames.ndim == 3:
        # grayscale frames, convert to RGB
        frames_rgb = np.stack([frames]*3, axis=-1)
    else:
        frames_rgb = frames
    pixels = frames_rgb.reshape(-1, 3)

    # Compute squared distance to palette colors
    dists = np.sum((pixels[:, None, :] - palette_arr[None, :, :]) ** 2, axis=2)
    indices = np.argmin(dists, axis=1).astype(np.uint8)
    indices = indices.reshape(frames.shape[:3])

    return palette, indices

def _write_gif(path, arr):
    # arr: (N,H,W) or (N,H,W,3) uint8
    # Write animated GIF with global palette.
    # Use minimal GIF89a format.
    # No transparency, no interlace, no extension blocks except Netscape loop extension.

    if arr.dtype != np.uint8:
        raise ValueError("Only uint8 arrays supported for GIF")
    if arr.ndim == 3:
        # grayscale frames
        frames = arr
    elif arr.ndim == 4 and arr.shape[3] == 3:
        frames = arr
    else:
        raise ValueError("Unsupported shape for GIF write: %s" % (arr.shape,))
    n_frames = frames.shape[0]
    height = frames.shape[1]
    width = frames.shape[2]

    palette, indices = _rgb_to_palette_and_indices(frames)

    def _pack_lzw(data):
        # Minimal LZW encoder for GIF with 8-bit codes
        # Use fixed 8-bit code size (minimum 8)
        # This is a very simple implementation, not optimized.
        # GIF LZW minimum code size is 8 for 8-bit palette.
        min_code_size = 8
        clear_code = 1 << min_code_size
        end_code = clear_code + 1
        code_size = min_code_size + 1
        max_code = (1 << code_size) - 1

        dict_size = end_code + 1
        dictionary = {bytes([i]): i for i in range(clear_code)}
        dictionary[bytes()] = None  # dummy

        result_bits = []
        bit_buffer = 0
        bit_count = 0

        def output_code(code):
            nonlocal bit_buffer, bit_count
            bit_buffer |= code << bit_count
            bit_count += code_size
            while bit_count >= 8:
                result_bits.append(bit_buffer & 0xFF)
                bit_buffer >>= 8
                bit_count -= 8

        output_code(clear_code)
        w = b""
        for k in data:
            wk = w + bytes([k])
            if wk in dictionary:
                w = wk
            else:
                output_code(dictionary[w])
                if dict_size <= max_code:
                    dictionary[wk] = dict_size
                    dict_size += 1
                else:
                    output_code(clear_code)
                    dictionary = {bytes([i]): i for i in range(clear_code)}
                    dict_size = end_code + 1
                w = bytes([k])
        if w:
            output_code(dictionary[w])
        output_code(end_code)
        if bit_count > 0:
            result_bits.append(bit_buffer & 0xFF)
        # Split into sub-blocks of max 255 bytes
        blocks = []
        i = 0
        while i < len(result_bits):
            block_len = min(255, len(result_bits) - i)
            blocks.append(bytes([block_len]) + bytes(result_bits[i:i+block_len]))
            i += block_len
        blocks.append(b'\x00')  # block terminator
        return b''.join(blocks)

    with open(path, "wb") as f:
        # Header
        f.write(b"GIF89a")
        # Logical Screen Descriptor
        f.write(struct.pack("<HH", width, height))
        # Packed fields:
        # Global Color Table Flag = 1
        # Color Resolution = 7 (bits per primary color - 1)
        # Sort Flag = 0
        # Size of Global Color Table = 7 (2^(7+1) = 256 colors)
        packed = 0b10000111
        f.write(bytes([packed]))
        f.write(b'\x00')  # Background Color Index
        f.write(b'\x00')  # Pixel Aspect Ratio

        # Global Color Table
        f.write(bytes(palette))

        # Netscape Looping Extension (infinite loop)
        f.write(b'\x21\xFF\x0BNETSCAPE2.0\x03\x01\x00\x00\x00')

        # Write frames
        for i in range(n_frames):
            # Graphic Control Extension
            f.write(b'\x21\xF9\x04')
            # Disposal Method=2 (restore to background), User Input Flag=0, Transparent Color Flag=0
            f.write(b'\x04')
            # Delay Time (in hundredths of seconds)
            f.write(struct.pack("<H", 5))  # 50ms delay
            # Transparent Color Index
            f.write(b'\x00')
            f.write(b'\x00')  # Block Terminator

            # Image Descriptor
            f.write(b'\x2C')
            # Image Left, Top, Width, Height
            f.write(struct.pack("<HHHH", 0, 0, width, height))
            # No local color table, no interlace
            f.write(b'\x00')

            # Image Data
            # Minimum LZW code size
            f.write(b'\x08')
            # LZW compressed image data
            frame_indices = indices[i].ravel()
            compressed = _pack_lzw(frame_indices)
            f.write(compressed)

        # Trailer
        f.write(b'\x3B')

def _read_gif(path):
    # Return ndarray uint8 with shape (N,H,W) or (N,H,W,3)
    # We only support non-interlaced, global palette GIFs with 8-bit palette.
    # We decode frames as palette indices and map to RGB.
    # If all palette colors are grayscale, return (N,H,W) uint8 grayscale.
    # Else return (N,H,W,3) uint8 RGB.

    with open(path, "rb") as f:
        data = f.read()

    if not data.startswith(b"GIF87a") and not data.startswith(b"GIF89a"):
        raise ValueError("Not a GIF file")

    # Parse Logical Screen Descriptor
    width, height = struct.unpack("<HH", data[6:10])
    packed = data[10]
    global_color_table_flag = (packed & 0x80) != 0
    color_resolution = ((packed & 0x70) >> 4) + 1
    sort_flag = (packed & 0x08) != 0
    size_of_global_color_table = packed & 0x07
    background_color_index = data[11]
    pixel_aspect_ratio = data[12]

    pos = 13
    if global_color_table_flag:
        gct_size = 3 * (2 ** (size_of_global_color_table + 1))
        global_color_table = data[pos:pos+gct_size]
        pos += gct_size
    else:
        raise ValueError("No global color table in GIF")

    frames = []
    delays = []
    while pos < len(data):
        block_id = data[pos]
        pos += 1
        if block_id == 0x21:
            # Extension block
            label = data[pos]
            pos += 1
            if label == 0xF9:
                # Graphic Control Extension
                block_size = data[pos]
                pos += 1
                gce_data = data[pos:pos+block_size]
                pos += block_size
                terminator = data[pos]
                pos += 1
                # We ignore disposal and transparency for now
            else:
                # Skip other extensions
                while True:
                    sub_block_size = data[pos]
                    pos += 1
                    if sub_block_size == 0:
                        break
                    pos += sub_block_size
        elif block_id == 0x2C:
            # Image Descriptor
            if pos + 9 > len(data):
                break
            left, top, w, h, packed_fields = struct.unpack("<HHHHB", data[pos:pos+9])
            pos += 9
            local_color_table_flag = (packed_fields & 0x80) != 0
            interlace_flag = (packed_fields & 0x40) != 0
            sort_flag = (packed_fields & 0x20) != 0
            size_of_local_color_table = packed_fields & 0x07
            if local_color_table_flag:
                lct_size = 3 * (2 ** (size_of_local_color_table + 1))
                local_color_table = data[pos:pos+lct_size]
                pos += lct_size
                palette = local_color_table
            else:
                palette = global_color_table
            # Image Data
            min_code_size = data[pos]
            pos += 1
            # Read image data sub-blocks
            compressed_data = bytearray()
            while True:
                block_size = data[pos]
                pos += 1
                if block_size == 0:
                    break
                compressed_data += data[pos:pos+block_size]
                pos += block_size
            # Decode LZW compressed image data
            frame_indices = _decode_lzw(bytes(compressed_data), min_code_size, w*h)
            frame = np.array(frame_indices, dtype=np.uint8).reshape((h, w))
            frames.append((frame, palette))
        elif block_id == 0x3B:
            # Trailer
            break
        else:
            # Unknown block, stop parsing
            break

    if not frames:
        raise ValueError("No frames found in GIF")

    # Determine if palette is grayscale
    def _palette_is_grayscale(pal):
        for i in range(0, len(pal), 3):
            r, g, b = pal[i:i+3]
            if r != g or g != b:
                return False
        return True

    # Convert frames to RGB or grayscale arrays
    n_frames = len(frames)
    h, w = frames[0][0].shape
    palette_bytes = frames[0][1]
    is_gray = _palette_is_grayscale(palette_bytes)
    palette_arr = np.frombuffer(palette_bytes, dtype=np.uint8).reshape((-1, 3))

    if is_gray:
        arr = np.empty((n_frames, h, w), dtype=np.uint8)
        for i, (frame_indices, _) in enumerate(frames):
            # Map indices to grayscale values
            vals = palette_arr[frame_indices, 0]
            arr[i] = vals
    else:
        arr = np.empty((n_frames, h, w, 3), dtype=np.uint8)
        for i, (frame_indices, _) in enumerate(frames):
            arr[i] = palette_arr[frame_indices]

    return arr

def _decode_lzw(data, min_code_size, expected_size):
    # Minimal LZW decoder for GIF
    # data: bytes of compressed data
    # min_code_size: int
    # expected_size: number of pixels expected in output
    # Returns list of indices

    clear_code = 1 << min_code_size
    end_code = clear_code + 1
    code_size = min_code_size + 1
    max_code = (1 << code_size) - 1

    # Initialize dictionary
    dict_size = end_code + 1
    dictionary = {i: bytes([i]) for i in range(clear_code)}
    dictionary[clear_code] = None
    dictionary[end_code] = None

    bit_pos = 0
    bit_len = len(data) * 8

    def get_code():
        nonlocal bit_pos
        code = 0
        bits_read = 0
        while bits_read < code_size and bit_pos < bit_len:
            byte_pos = bit_pos // 8
            bit_offset = bit_pos % 8
            bits_left = 8 - bit_offset
            bits_to_read = min(bits_left, code_size - bits_read)
            mask = (1 << bits_to_read) - 1
            bits = (data[byte_pos] >> bit_offset) & mask
            code |= bits << bits_read
            bits_read += bits_to_read
            bit_pos += bits_to_read
        if bits_read < code_size:
            return None
        return code

    result = bytearray()
    prev_code = None
    while True:
        code = get_code()
        if code is None:
            break
        if code == clear_code:
            dictionary = {i: bytes([i]) for i in range(clear_code)}
            dictionary[clear_code] = None
            dictionary[end_code] = None
            dict_size = end_code + 1
            code_size = min_code_size + 1
            max_code = (1 << code_size) - 1
            prev_code = None
            continue
        if code == end_code:
            break
        if code in dictionary:
            entry = dictionary[code]
            if prev_code is not None:
                dictionary[dict_size] = dictionary[prev_code] + entry[:1]
                dict_size += 1
        elif code == dict_size:
            entry = dictionary[prev_code] + dictionary[prev_code][:1]
            dictionary[dict_size] = entry
            dict_size += 1
        else:
            raise ValueError("Invalid LZW code")
        result.extend(entry)
        prev_code = code
        if dict_size > max_code and code_size < 12:
            code_size += 1
            max_code = (1 << code_size) - 1
        if len(result) >= expected_size:
            break
    return list(result[:expected_size])

def _is_animated_gif(path):
    # Quick check if GIF is animated by counting image descriptors
    try:
        with open(path, "rb") as f:
            data = f.read()
        if not data.startswith(b"GIF87a") and not data.startswith(b"GIF89a"):
            return False
        count = 0
        pos = 13
        packed = data[10]
        global_color_table_flag = (packed & 0x80) != 0
        size_of_global_color_table = packed & 0x07
        if global_color_table_flag:
            gct_size = 3 * (2 ** (size_of_global_color_table + 1))
            pos += gct_size
        while pos < len(data):
            block_id = data[pos]
            pos += 1
            if block_id == 0x2C:
                count += 1
                pos += 9
                packed_fields = data[pos - 1]
                local_color_table_flag = (packed_fields & 0x80) != 0
                size_of_local_color_table = packed_fields & 0x07
                if local_color_table_flag:
                    lct_size = 3 * (2 ** (size_of_local_color_table + 1))
                    pos += lct_size
                # Skip image data
                min_code_size = data[pos]
                pos += 1
                while True:
                    block_size = data[pos]
                    pos += 1
                    if block_size == 0:
                        break
                    pos += block_size
            elif block_id == 0x3B:
                break
            elif block_id == 0x21:
                # Extension block
                label = data[pos]
                pos += 1
                while True:
                    sub_block_size = data[pos]
                    pos += 1
                    if sub_block_size == 0:
                        break
                    pos += sub_block_size
            else:
                break
        return count > 1
    except Exception:
        return False

def _is_png(path):
    try:
        with open(path, "rb") as f:
            sig = f.read(8)
        return sig == _PNG_SIGNATURE
    except Exception:
        return False

def _is_gif(path):
    try:
        with open(path, "rb") as f:
            sig = f.read(6)
        return sig in (b"GIF87a", b"GIF89a")
    except Exception:
        return False

class ImageProps:
    def __init__(self, shape, dtype):
        self.shape = shape
        self.dtype = dtype

def imwrite(uri, image):
    # Accept filesystem path (str or Path) and numpy array
    # Determine if single image or animated
    path = Path(uri)
    arr = np.asarray(image)
    if arr.dtype != np.uint8:
        raise ValueError("Only uint8 arrays supported")

    if arr.ndim == 2 or (arr.ndim == 3 and arr.shape[2] in (1, 3)):
        # Single image
        # Write PNG
        _write_png(path, arr)
    elif arr.ndim == 3 and arr.shape[0] > 1 and arr.shape[1] and arr.shape[2]:
        # Could be (N,H,W) grayscale animated
        # Write GIF
        _write_gif(path, arr)
    elif arr.ndim == 4 and arr.shape[0] > 1 and arr.shape[1] and arr.shape[2] and arr.shape[3] in (1, 3):
        # (N,H,W,C) animated
        # Convert (N,H,W,1) to (N,H,W)
        if arr.shape[3] == 1:
            arr = arr.reshape(arr.shape[0], arr.shape[1], arr.shape[2])
        _write_gif(path, arr)
    else:
        raise ValueError("Unsupported image shape for imwrite: %s" % (arr.shape,))

def imread(uri):
    path = Path(uri)
    if _is_png(path):
        arr = _read_png(path)
        return arr
    elif _is_gif(path):
        arr = _read_gif(path)
        if arr.shape[0] == 1:
            # Return single frame as 2D or 3D array
            return arr[0]
        else:
            # Return first frame only for imread
            return arr[0]
    else:
        raise ValueError("Unsupported image format for imread")

def imiter(uri):
    path = Path(uri)
    if _is_png(path):
        arr = _read_png(path)
        yield arr
    elif _is_gif(path):
        arr = _read_gif(path)
        for frame in arr:
            yield frame
    else:
        raise ValueError("Unsupported image format for imiter")

def improps(uri):
    path = Path(uri)
    if _is_png(path):
        arr = _read_png(path)
        return ImageProps(arr.shape, arr.dtype)
    elif _is_gif(path):
        arr = _read_gif(path)
        return ImageProps(arr.shape, arr.dtype)
    else:
        raise ValueError("Unsupported image format for improps")

def immeta(uri):
    path = Path(uri)
    if _is_png(path):
        arr = _read_png(path)
        if arr.ndim == 2:
            mode = "L"
        elif arr.ndim == 3 and arr.shape[2] == 3:
            mode = "RGB"
        else:
            mode = "Unknown"
        return {"mode": mode}
    elif _is_gif(path):
        # GIF mode is "P" (palette)
        return {"mode": "P"}
    else:
        raise ValueError("Unsupported image format for immeta")