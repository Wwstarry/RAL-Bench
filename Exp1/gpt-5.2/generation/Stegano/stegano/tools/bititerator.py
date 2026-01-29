from __future__ import annotations

from typing import Iterable, Iterator


def bits_from_bytes(data: bytes) -> Iterator[int]:
    """
    Yield bits MSB->LSB for each byte in data.
    """
    for byte in data:
        for i in range(7, -1, -1):
            yield (byte >> i) & 1


def bytes_from_bits(bits: Iterable[int]) -> Iterator[int]:
    """
    Consume bits (ints 0/1) and yield bytes (ints 0-255).
    Extra bits not forming a full byte are ignored.
    """
    acc = 0
    n = 0
    for b in bits:
        acc = (acc << 1) | (1 if b else 0)
        n += 1
        if n == 8:
            yield acc
            acc = 0
            n = 0