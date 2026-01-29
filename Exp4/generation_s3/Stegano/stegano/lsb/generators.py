from __future__ import annotations

from typing import Iterator


def eratosthenes() -> Iterator[int]:
    """
    Infinite generator yielding prime numbers in ascending order.

    Used by the LSB backend as a pixel-index generator.
    """
    # Incremental sieve (dictionary of composites -> step)
    # Based on a common "incremental Sieve of Eratosthenes" implementation.
    D: dict[int, int] = {}
    q = 2
    while True:
        if q not in D:
            yield q
            D[q * q] = q
        else:
            p = D.pop(q)
            x = q + p
            while x in D:
                x += p
            D[x] = p
        q += 1