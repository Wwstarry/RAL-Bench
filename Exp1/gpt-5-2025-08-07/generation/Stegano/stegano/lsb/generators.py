from typing import Iterator

def eratosthenes() -> Iterator[int]:
    """
    Generator yielding prime numbers using the Sieve of Eratosthenes concept.
    Yields integers starting from 2: 2, 3, 5, 7, 11, ...
    This is a simple incremental prime generator suitable for selecting
    positions in LSB steganography.
    """
    D = {}
    q = 2
    while True:
        if q not in D:
            # q is a new prime.
            yield q
            D[q * q] = [q]
        else:
            for p in D[q]:
                D.setdefault(p + q, []).append(p)
            del D[q]
        q += 1