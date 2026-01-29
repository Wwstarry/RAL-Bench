from __future__ import annotations

from collections.abc import Iterator


def eratosthenes() -> Iterator[int]:
    """
    Infinite generator of prime numbers: 2, 3, 5, 7, ...

    Uses an incremental sieve (often called the "dictionary" sieve).
    """
    D: dict[int, list[int]] = {}
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