# stegano/tools/utils.py
from stegano.tools.bititerator import bits

# Delimiter to mark the end of the hidden message.
# It's a sequence of 8 null bits.
DELIMITER = [0, 0, 0, 0, 0, 0, 0, 0]

def bits_to_bytes(bit_list):
    """Convert a list of bits to a byte string."""
    if len(bit_list) % 8 != 0:
        raise ValueError("The length of the bit list must be a multiple of 8.")
    
    byte_array = bytearray()
    for i in range(0, len(bit_list), 8):
        byte = 0
        for j in range(8):
            byte = (byte << 1) | bit_list[i + j]
        byte_array.append(byte)
    return bytes(byte_array)

def get_bit_generator(message_str, encoding="UTF-8"):
    """
    Returns a generator that yields the bits of the message,
    followed by the delimiter.
    """
    encoded_message = message_str.encode(encoding)
    
    # Yield bits from the message
    yield from bits(encoded_message)
    
    # Yield bits from the delimiter
    for bit in DELIMITER:
        yield bit