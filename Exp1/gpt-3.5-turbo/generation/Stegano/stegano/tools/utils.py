from typing import Iterator, List


def text_to_bits(data: bytes) -> Iterator[int]:
    """
    Convert bytes to iterator of bits (MSB first).
    """
    for byte in data:
        for i in range(7, -1, -1):
            yield (byte >> i) & 1


def bits_to_text(bits: List[int]) -> bytes:
    """
    Convert list of bits (MSB first) to bytes.
    """
    bytes_out = bytearray()
    for i in range(0, len(bits), 8):
        byte_bits = bits[i:i + 8]
        if len(byte_bits) < 8:
            break
        byte = 0
        for bit in byte_bits:
            byte = (byte << 1) | bit
        bytes_out.append(byte)
    return bytes(bytes_out)