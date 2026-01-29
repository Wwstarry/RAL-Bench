"""
Generators for LSB steganography
"""
import itertools
from typing import Iterator


def eratosthenes() -> Iterator[int]:
    """
    Sieve of Eratosthenes generator yielding prime numbers
    
    Returns:
        Iterator of prime numbers starting from 2
    """
    D = {}
    q = 2
    
    while True:
        if q not in D:
            yield q
            D[q * q] = [q]
        else:
            for p in D[q]:
                D.setdefault(p + q, []).append(p)
            del D[q]
        q += 1