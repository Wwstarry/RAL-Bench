class BitIterator:
    def __init__(self, data):
        self.data = data
        self.byte_index = 0
        self.bit_index = 7
    
    def __iter__(self):
        return self
    
    def __next__(self):
        if self.byte_index >= len(self.data):
            raise StopIteration
        
        byte = self.data[self.byte_index]
        bit = (byte >> self.bit_index) & 1
        
        self.bit_index -= 1
        if self.bit_index < 0:
            self.bit_index = 7
            self.byte_index += 1
        
        return bit