"""
stegano.lsb.generators – Collection of generator factories that define the
order in which pixels are processed when hiding / revealing data.
"""
from __future__ import annotations

import itertools
import math
from typing import Iterator


def eratosthenes() -> Iterator[int]:
    """
    Infinite generator that yields prime numbers in ascending order using the
    sieve of Eratosthenes.  It can be used as a *generator* parameter for
    :pyfunc:`stegano.lsb.hide` / :pyfunc:`stegano.lsb.reveal` to distribute the
    payload over pseudo random-looking pixel positions.
    """
    yield 2
    sieve: dict[int, list[int]] = {}
    for num in itertools.count(3, 2):  # odd numbers only
        if num not in sieve:
            yield num
            sieve[num * num] = [num]
        else:
            for p in sieve[num]:
                sieve.setdefault(p + num * 2, []).append(p)
            del sieve[num]