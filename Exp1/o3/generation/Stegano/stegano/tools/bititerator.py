"""
BitReader & BitWriter – simple helpers for dealing with single-bit IO
"""
from __future__ import annotations

from typing import Iterator, List, Sequence


class BitWriter:
    """
    Consumes bits from *source* on demand.

    Example:
        writer = BitWriter([1,0,1])
        bit = writer.read_bit()
    """

    def __init__(self, source: Sequence[int] | Iterator[int]):
        self._iter = iter(source)

    def read_bit(self) -> int:
        return next(self._iter)


class BitReader:
    """
    Collects bits and converts them back to bytes once *count* bits were read.
    Not used by the current implementation but provided for completeness.
    """

    def __init__(self):
        self._bits: List[int] = []

    def push(self, bit: int) -> None:
        self._bits.append(bit)

    def to_bytes(self) -> bytes:
        from .utils import bytes_from_bits

        return bytes_from_bits(self._bits)