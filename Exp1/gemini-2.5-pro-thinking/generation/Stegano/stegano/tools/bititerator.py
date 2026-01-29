from typing import Iterator

def bits_from_bytes(data: bytes) -> Iterator[int]:
    """
    Generator that yields the bits from a byte string.
    """
    for byte in data:
        for i in range(8):
            yield (byte >> (7 - i)) & 1