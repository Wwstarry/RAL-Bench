from __future__ import annotations

from typing import Any, Union, Tuple
from pathlib import Path
from PIL import Image


def uint32be_pack(n: int) -> bytes:
    if n < 0 or n > 0xFFFFFFFF:
        raise ValueError("uint32 out of range")
    return bytes(((n >> 24) & 0xFF, (n >> 16) & 0xFF, (n >> 8) & 0xFF, n & 0xFF))


def uint32be_unpack(b4: bytes) -> int:
    if len(b4) != 4:
        raise ValueError("Need exactly 4 bytes for uint32")
    return (b4[0] << 24) | (b4[1] << 16) | (b4[2] << 8) | b4[3]


def frame_payload(payload: bytes) -> bytes:
    """Length-prefix framing: 4-byte big-endian length + payload."""
    return uint32be_pack(len(payload)) + payload


def ensure_image(obj: Union[str, Path, Image.Image]) -> Image.Image:
    if isinstance(obj, Image.Image):
        return obj
    return Image.open(obj)


def parse_length_prefix_from_bits(bits_iter) -> tuple[int, int]:
    """
    Read a 4-byte big-endian length from a bit iterator.
    Returns (length, bits_consumed).
    """
    length_bits = [next(bits_iter) for _ in range(32)]
    # build bytes
    acc = 0
    out = bytearray()
    for i, bit in enumerate(length_bits, start=1):
        acc = (acc << 1) | (1 if bit else 0)
        if i % 8 == 0:
            out.append(acc & 0xFF)
            acc = 0
    length = uint32be_unpack(bytes(out))
    return length, 32


def validate_length_against_capacity_bytes(length: int, remaining_capacity_bits: int) -> None:
    if length < 0:
        raise ValueError("Invalid embedded length.")
    max_bytes = remaining_capacity_bits // 8
    if length > max_bytes:
        raise ValueError("Invalid embedded length (exceeds capacity). Possible wrong key/generator or corrupt data.")