import itertools

def eratosthenes():
    """
    Yields prime numbers using the Sieve of Eratosthenes.
    """
    # Start from 2
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