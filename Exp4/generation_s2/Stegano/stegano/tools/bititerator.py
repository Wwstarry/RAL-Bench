from __future__ import annotations

from typing import Iterable, Iterator, List


def bits_from_bytes(data: bytes) -> Iterator[int]:
    """Yield bits (0/1) MSB-first for each byte in data."""
    for b in data:
        for i in range(7, -1, -1):
            yield (b >> i) & 1


def bytes_from_bits(bits: Iterable[int]) -> Iterator[int]:
    """Group bits (MSB-first) into bytes, yielding ints 0..255."""
    acc = 0
    n = 0
    for bit in bits:
        acc = (acc << 1) | (1 if bit else 0)
        n += 1
        if n == 8:
            yield acc
            acc = 0
            n = 0
    if n != 0:
        # ignore trailing incomplete byte (should not happen in this library)
        return


def int_to_bits(value: int, width: int) -> List[int]:
    """Return a list of bits (MSB-first) for an integer."""
    if width <= 0:
        return []
    return [((value >> (width - 1 - i)) & 1) for i in range(width)]