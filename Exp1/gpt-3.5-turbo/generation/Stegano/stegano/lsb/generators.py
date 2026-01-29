from typing import Iterator


def eratosthenes() -> Iterator[int]:
    """
    Generator yielding prime numbers starting from 2.
    Used as pixel indices for hiding bits in LSB steganography.
    """
    D = {}
    q = 2
    while True:
        if q not in D:
            # q is a new prime.
            yield q - 2  # zero-based index, so subtract 2 to start from 0
            D[q * q] = [q]
        else:
            for p in D[q]:
                D.setdefault(p + q, []).append(p)
            del D[q]
        q += 1