from __future__ import annotations

from typing import Iterable, Iterator, List, Sequence


def bits_from_bytes(data: bytes) -> Iterator[int]:
    """
    Yield bits (0/1) MSB-first for each byte in data.
    """
    for b in data:
        for i in range(7, -1, -1):
            yield (b >> i) & 1


def bytes_from_bits(bits: Sequence[int]) -> bytes:
    """
    Convert exactly 8 bits (MSB-first) into a single byte.
    """
    if len(bits) != 8:
        raise ValueError("bytes_from_bits requires exactly 8 bits")
    val = 0
    for bit in bits:
        val = (val << 1) | (1 if bit else 0)
    return bytes([val])


def iter_bytes_from_bitstream(bitstream: Iterable[int]) -> Iterator[int]:
    """
    Consume a bit iterable and yield reconstructed bytes (as ints 0..255).
    """
    buf: List[int] = []
    for bit in bitstream:
        buf.append(1 if bit else 0)
        if len(buf) == 8:
            yield bytes_from_bits(buf)[0]
            buf.clear()