class BitIterator:
    """
    Iterator to iterate over bits of an integer or bytes.
    """
    def __init__(self, value, length=8):
        self.value = value
        self.length = length
        self.current = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.current < self.length:
            # Extract bit from MSB to LSB usually, but standard steganography 
            # often encodes characters MSB first.
            # Let's assume standard big-endian bit extraction for the byte.
            bit = (self.value >> (self.length - 1 - self.current)) & 1
            self.current += 1
            return bit
        raise StopIteration