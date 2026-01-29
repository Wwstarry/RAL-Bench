from __future__ import annotations

from typing import Iterator


def eratosthenes() -> Iterator[int]:
    """
    Infinite generator of prime numbers (2, 3, 5, 7, ...).
    Used as a deterministic position generator in LSB backend.
    """
    yield 2
    # Map composite -> step (its prime factor)
    composites: dict[int, int] = {}
    n = 3
    while True:
        step = composites.pop(n, None)
        if step is None:
            yield n
            composites[n * n] = 2 * n
        else:
            nxt = n + step
            while nxt in composites:
                nxt += step
            composites[nxt] = step
        n += 2