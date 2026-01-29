"""
Generators for pixel indices, e.g. primes-based generator (eratosthenes).
"""
from typing import Iterator


def eratosthenes() -> Iterator[int]:
    """
    Prime generator using the Sieve of Eratosthenes.
    Yields prime indices which can be used as positions in LSB steganography.
    """
    D = {}
    q = 2
    while True:
        if q not in D:
            # q is prime
            yield q
            D[q*q] = [q]
        else:
            for p in D[q]:
                D.setdefault(p+q, []).append(p)
            del D[q]
        q += 1