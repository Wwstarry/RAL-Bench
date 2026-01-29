"""
Utility functions for converting between ints, bytes, and bits.
"""
from typing import List


def int_to_bytes(value: int, length: int) -> bytes:
    return value.to_bytes(length, byteorder="big")


def bytes_to_int(b: bytes) -> int:
    return int.from_bytes(b, byteorder="big")


def bytes_to_bits(b: bytes) -> List[int]:
    bits = []
    for byte in b:
        for i in range(8):
            bits.append((byte >> i) & 1)
    return bits


def bits_to_bytes(bits: List[int]) -> bytes:
    # bits come in LSB order (bit 0 = lowest)
    # We'll reconstruct per group of 8
    if len(bits) % 8 != 0:
        raise ValueError("Number of bits must be multiple of 8.")
    out = bytearray()
    for i in range(0, len(bits), 8):
        byte_val = 0
        for b in range(8):
            byte_val |= (bits[i+b] << b)
        out.append(byte_val)
    return bytes(out)