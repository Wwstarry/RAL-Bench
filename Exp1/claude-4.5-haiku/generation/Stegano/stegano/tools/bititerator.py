"""
Bit iterator utility for steganography
"""


class BitIterator:
    """Iterator for extracting bits from data"""
    
    def __init__(self, data):
        """
        Initialize BitIterator.
        
        Args:
            data: Bytes or bytearray to iterate over
        """
        self.data = data
        self.bit_index = 0
    
    def __iter__(self):
        return self
    
    def __next__(self):
        """Get next bit"""
        byte_index = self.bit_index // 8
        bit_position = 7 - (self.bit_index % 8)
        
        if byte_index >= len(self.data):
            raise StopIteration
        
        bit = (self.data[byte_index] >> bit_position) & 1
        self.bit_index += 1
        
        return bit
    
    def reset(self):
        """Reset iterator to beginning"""
        self.bit_index = 0