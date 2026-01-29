"""
Generic helpers for bit / bytes conversion.
"""
from __future__ import annotations

from typing import List, Sequence


def bits_from_bytes(data: bytes | bytearray) -> List[int]:
    """Converts *data* to a list of bits (big-endian per byte)."""
    bits: List[int] = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def bytes_from_bits(bits: Sequence[int]) -> bytes:
    """Converts a sequence of bits (multiple of 8) back to bytes."""
    if len(bits) % 8 != 0:
        raise ValueError("Number of bits must be a multiple of 8")
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | (bits[i + j] & 1)
        out.append(byte)
    return bytes(out)