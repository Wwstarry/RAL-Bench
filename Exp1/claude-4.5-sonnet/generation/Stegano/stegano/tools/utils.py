"""
Utility functions
"""


def binary_to_string(binary_data, encoding='UTF-8'):
    """
    Convert binary data to string.
    
    Args:
        binary_data: Bytes to convert
        encoding: Text encoding
        
    Returns:
        Decoded string
    """
    return binary_data.decode(encoding, errors='ignore')


def string_to_binary(text, encoding='UTF-8'):
    """
    Convert string to binary data.
    
    Args:
        text: String to convert
        encoding: Text encoding
        
    Returns:
        Encoded bytes
    """
    return text.encode(encoding)


def bytes_to_bits(data):
    """
    Convert bytes to list of bits.
    
    Args:
        data: Bytes to convert
        
    Returns:
        List of 0s and 1s
    """
    bits = []
    for byte in data:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1)
    return bits


def bits_to_bytes(bits):
    """
    Convert list of bits to bytes.
    
    Args:
        bits: List of 0s and 1s
        
    Returns:
        Bytearray
    """
    result = bytearray()
    for i in range(0, len(bits), 8):
        if i + 8 <= len(bits):
            byte_val = 0
            for j in range(8):
                byte_val = (byte_val << 1) | bits[i + j]
            result.append(byte_val)
    return result