from typing import Iterator, Iterable


class BitIterator:
    """
    Iterator over bits of bytes or iterable of ints.
    Yields bits MSB first for each byte.
    """

    def __init__(self, data: Iterable[int]):
        self.data = iter(data)
        self.current_byte = None
        self.bits_left = 0

    def __iter__(self) -> Iterator[int]:
        return self

    def __next__(self) -> int:
        if self.bits_left == 0:
            self.current_byte = next(self.data)
            self.bits_left = 8
        self.bits_left -= 1
        return (self.current_byte >> self.bits_left) & 1