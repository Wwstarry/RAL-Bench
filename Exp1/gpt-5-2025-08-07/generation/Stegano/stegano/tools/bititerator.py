from typing import Iterable, List

def bytes_to_bits(data: bytes) -> List[int]:
    """
    Convert bytes to a list of bits (big-endian within each byte).
    """
    bits: List[int] = []
    for b in data:
        for i in range(7, -1, -1):
            bits.append((b >> i) & 1)
    return bits

def bits_to_bytes(bits: Iterable[int]) -> bytes:
    """
    Convert an iterable of bits (big-endian within each byte) to bytes.
    Truncates any trailing bits not forming a full byte.
    """
    out = bytearray()
    acc = 0
    count = 0
    for bit in bits:
        acc = (acc << 1) | (bit & 1)
        count += 1
        if count == 8:
            out.append(acc & 0xFF)
            acc = 0
            count = 0
    return bytes(out)