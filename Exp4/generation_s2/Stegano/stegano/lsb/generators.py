from __future__ import annotations

from typing import Iterator


def eratosthenes() -> Iterator[int]:
    """
    Prime-number generator (Sieve of Eratosthenes style), returning an infinite
    sequence of primes: 2, 3, 5, 7, 11, ...

    This is used by the LSB backend as an index generator for pixel positions.
    """
    # Incremental sieve
    composites = {}
    n = 2
    while True:
        step = composites.pop(n, None)
        if step is None:
            # n is prime
            yield n
            composites[n * n] = n
        else:
            nxt = n + step
            while nxt in composites:
                nxt += step
            composites[nxt] = step
        n += 1