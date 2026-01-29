def bit_iterator(data):
    for byte in data:
        for i in range(8):
            yield (byte >> i) & 1