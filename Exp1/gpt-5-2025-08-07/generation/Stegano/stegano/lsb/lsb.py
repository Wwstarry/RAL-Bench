from typing import Iterator, List, Optional, Sequence, Tuple, Union
from PIL import Image
from ..tools.utils import (
    ensure_image_mode,
    message_to_bytes,
    int_to_bits_be,
    bits_to_int_be,
    bytes_to_bits,
    bits_to_bytes,
    get_channel_indices,
    image_pixels_as_tuples,
    put_pixels_from_tuples,
)

def _compute_slots_count(img: Image.Image) -> Tuple[int, List[int], List[Tuple[int, ...]]]:
    """
    Returns (slots_count, channel_indices, pixels)
    where slots_count = number of usable channels across all pixels.
    """
    pixels = image_pixels_as_tuples(img)
    bands = img.getbands()
    channel_indices = get_channel_indices(bands)
    slots_count = len(pixels) * len(channel_indices)
    return slots_count, channel_indices, pixels

def _slot_to_pixel_channel(slot_index: int, channels_count: int) -> Tuple[int, int]:
    """
    Map a slot index to (pixel_index, channel_index_in_channel_indices_list).
    """
    pixel_index = slot_index // channels_count
    channel_index = slot_index % channels_count
    return pixel_index, channel_index

def _collect_positions_for_bits(
    total_slots: int,
    num_bits: int,
    shift: int,
    generator: Optional[Iterator[int]],
) -> List[int]:
    """
    Build a list of slot positions (indices) where bits will be embedded/read.
    If generator is None, positions are sequential from shift.
    Else, positions are generator yields offset by shift; stop when enough or capacity reached.
    """
    if generator is None:
        end = shift + num_bits
        if end > total_slots:
            raise ValueError("Not enough capacity to hide the message using sequential slots.")
        return list(range(shift, end))
    positions: List[int] = []
    # We treat generator yields as 0-based positions; add shift to target slot index.
    # For primes generator starting at 2, we still add shift; any s >= total_slots ends the availability.
    for pos in generator:
        s = shift + pos
        if s >= total_slots:
            # No more usable positions
            break
        positions.append(s)
        if len(positions) >= num_bits:
            break
    if len(positions) < num_bits:
        raise ValueError("Not enough capacity to hide the message using provided generator.")
    return positions

def hide(
    image: Image.Image,
    message: Union[str, bytes],
    generator: Optional[Iterator[int]] = None,
    shift: int = 0,
    encoding: str = "UTF-8",
    auto_convert_rgb: bool = False,
) -> Image.Image:
    """
    Hide a text/byte message inside the least significant bits of image channels.
    - If generator is provided, it selects the slot indices to modify (offset by 'shift').
    - Otherwise, slots are used sequentially starting from 'shift'.
    The message is stored with a 32-bit big-endian length prefix to allow extraction.
    """
    if not isinstance(image, Image.Image):
        raise TypeError("image must be a PIL.Image.Image instance")
    img = ensure_image_mode(image, auto_convert_rgb=auto_convert_rgb)

    msg_bytes = message_to_bytes(message, encoding)
    payload_bits = bytes_to_bits(msg_bytes)
    length_bits = int_to_bits_be(len(msg_bytes), 32)
    full_bits = length_bits + payload_bits

    total_slots, channel_indices, pixels = _compute_slots_count(img)
    channels_count = len(channel_indices)
    if channels_count == 0:
        raise ValueError("No usable image channels found for LSB steganography.")

    positions = _collect_positions_for_bits(total_slots, len(full_bits), shift, generator)

    # Prepare mutable copy of pixels
    mutable_pixels: List[List[int]] = [list(p) for p in pixels]

    for i, bit in enumerate(full_bits):
        slot = positions[i]
        pixel_index, chan_index_in_list = _slot_to_pixel_channel(slot, channels_count)
        chan_abs_index = channel_indices[chan_index_in_list]
        original_value = mutable_pixels[pixel_index][chan_abs_index]
        mutable_pixels[pixel_index][chan_abs_index] = (original_value & ~1) | (bit & 1)

    # Rebuild image
    new_pixels_tuples: List[Tuple[int, ...]] = [tuple(p) for p in mutable_pixels]
    new_img = img.copy()
    put_pixels_from_tuples(new_img, new_pixels_tuples)
    return new_img

def reveal(
    image: Image.Image,
    generator: Optional[Iterator[int]] = None,
    shift: int = 0,
    encoding: str = "UTF-8",
) -> str:
    """
    Reveal a hidden message from the image LSBs using the same generator/shift used for hiding.
    Reads a 32-bit big-endian length prefix followed by that many bytes.
    Returns the decoded string using the provided encoding (UTF-8 by default).
    """
    if not isinstance(image, Image.Image):
        raise TypeError("image must be a PIL.Image.Image instance")
    img = ensure_image_mode(image, auto_convert_rgb=False)

    total_slots, channel_indices, pixels = _compute_slots_count(img)
    channels_count = len(channel_indices)
    if channels_count == 0:
        return ""

    # First read 32 bits for the length prefix
    length_positions = _collect_positions_for_bits(total_slots, 32, shift, generator)
    length_bits: List[int] = []
    for s in length_positions:
        pixel_index, chan_index_in_list = _slot_to_pixel_channel(s, channels_count)
        chan_abs_index = channel_indices[chan_index_in_list]
        value = pixels[pixel_index][chan_abs_index]
        length_bits.append(value & 1)
    msg_len = bits_to_int_be(length_bits)

    # Now read msg_len bytes (msg_len * 8 bits)
    payload_bits_count = msg_len * 8
    payload_positions = _collect_positions_for_bits(total_slots, 32 + payload_bits_count, shift, generator)
    # We've already consumed first 32 positions: skip them
    payload_positions = payload_positions[32:]
    payload_bits: List[int] = []
    for s in payload_positions:
        pixel_index, chan_index_in_list = _slot_to_pixel_channel(s, channels_count)
        chan_abs_index = channel_indices[chan_index_in_list]
        value = pixels[pixel_index][chan_abs_index]
        payload_bits.append(value & 1)

    msg_bytes = bits_to_bytes(payload_bits)
    try:
        return msg_bytes.decode(encoding, errors="strict")
    except Exception:
        # Fallback to replace invalid sequences
        return msg_bytes.decode(encoding, errors="replace")