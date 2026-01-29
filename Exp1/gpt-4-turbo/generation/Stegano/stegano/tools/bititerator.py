class BitIterator:
    def __init__(self, data):
        self.data = data
        self.byte_idx = 0
        self.bit_idx = 0

    def __iter__(self):
        return self

    def __next__(self):
        if self.byte_idx >= len(self.data):
            raise StopIteration
        byte = self.data[self.byte_idx]
        bit = (byte >> (7 - self.bit_idx)) & 1
        self.bit_idx += 1
        if self.bit_idx == 8:
            self.bit_idx = 0
            self.byte_idx += 1
        return bit