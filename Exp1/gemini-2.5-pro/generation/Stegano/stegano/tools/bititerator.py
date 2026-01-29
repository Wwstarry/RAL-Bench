# stegano/tools/bititerator.py
"""
A tool to iterate over the bits of a bytes-like object.
"""

def bits(data):
    """
    A generator that yields the bits of a bytes-like object.
    
    Args:
        data (bytes): The input data.
        
    Yields:
        int: The next bit (0 or 1).
    """
    for byte in data:
        for i in range(8):
            yield (byte >> (7 - i)) & 1