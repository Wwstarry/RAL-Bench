from __future__ import annotations

from collections.abc import Iterable, Iterator


def bytes_to_bits(data: bytes) -> Iterator[int]:
    """Yield bits MSB-first for each byte."""
    for b in data:
        for i in range(7, -1, -1):
            yield (b >> i) & 1


def bits_to_bytes(bits: Iterable[int]) -> bytes:
    """Pack bits (MSB-first per byte) into bytes. Extra bits are ignored if not multiple of 8."""
    out = bytearray()
    acc = 0
    n = 0
    for bit in bits:
        acc = (acc << 1) | (1 if bit else 0)
        n += 1
        if n == 8:
            out.append(acc & 0xFF)
            acc = 0
            n = 0
    return bytes(out)