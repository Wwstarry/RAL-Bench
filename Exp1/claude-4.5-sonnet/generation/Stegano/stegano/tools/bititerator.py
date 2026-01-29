"""
Bit iterator utility
"""


class BitIterator:
    """
    Iterator for bits in a byte sequence
    """
    
    def __init__(self, data):
        """
        Initialize bit iterator.
        
        Args:
            data: Bytes or bytearray to iterate over
        """
        self.data = data
        self.byte_index = 0
        self.bit_index = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        """
        Get next bit.
        
        Returns:
            0 or 1
        """
        if self.byte_index >= len(self.data):
            raise StopIteration
        
        byte = self.data[self.byte_index]
        bit = (byte >> (7 - self.bit_index)) & 1
        
        self.bit_index += 1
        if self.bit_index == 8:
            self.bit_index = 0
            self.byte_index += 1
        
        return bit